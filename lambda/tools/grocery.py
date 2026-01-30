"""Grocery list and ordering tools"""
from typing import List, Optional

from tools.base import BaseTool, ToolResult
from memory.models import GroceryItem, Order, OrderItem, OrderStatus


class AddToGroceryListTool(BaseTool):
    name = "add_to_grocery_list"
    description = "Add items to the household grocery list"
    parameters = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit": {"type": "string"}
                    },
                    "required": ["name"]
                },
                "description": "List of items to add"
            }
        },
        "required": ["items"]
    }
    
    def __init__(self, storage, user_id: str, added_by: str):
        self.storage = storage
        self.user_id = user_id
        self.added_by = added_by
    
    def execute(self, items: List[dict]) -> ToolResult:
        """Add items to grocery list"""
        
        try:
            added_items = []
            
            for item_data in items:
                item = GroceryItem(
                    user_id=self.user_id,
                    item_name=item_data["name"],
                    quantity=item_data.get("quantity", 1),
                    unit=item_data.get("unit"),
                    added_by=self.added_by
                )
                saved = self.storage.add_to_grocery_list(item)
                added_items.append(saved.item_name)
            
            return ToolResult(
                success=True,
                data={"added": added_items},
                message=f"Added {len(added_items)} item(s) to grocery list: {', '.join(added_items)}"
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ViewGroceryListTool(BaseTool):
    name = "view_grocery_list"
    description = "View the current grocery list"
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    def __init__(self, storage, user_id: str):
        self.storage = storage
        self.user_id = user_id
    
    def execute(self) -> ToolResult:
        """Get grocery list"""
        
        try:
            items = self.storage.get_grocery_list(self.user_id)
            
            if not items:
                return ToolResult(
                    success=True,
                    data={"items": []},
                    message="The grocery list is empty"
                )
            
            item_list = []
            for item in items:
                qty_str = f"{item.quantity} {item.unit}" if item.unit else str(int(item.quantity))
                item_list.append({
                    "name": item.item_name,
                    "quantity": qty_str
                })
            
            # Create readable list
            item_names = [f"{i['name']} ({i['quantity']})" for i in item_list]
            
            return ToolResult(
                success=True,
                data={"items": item_list},
                message=f"Grocery list has {len(items)} items: {', '.join(item_names)}"
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CreateOrderRequestTool(BaseTool):
    name = "create_order_request"
    description = "Create an order request for groceries or medicines. This will be sent for approval."
    parameters = {
        "type": "object",
        "properties": {
            "order_type": {
                "type": "string",
                "enum": ["grocery", "medicine"],
                "description": "Type of order"
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit": {"type": "string"},
                        "estimated_price": {"type": "number"}
                    },
                    "required": ["name"]
                },
                "description": "Items to order"
            },
            "platform": {
                "type": "string",
                "enum": ["zepto", "blinkit", "bigbasket", "pharmeasy", "1mg", "other"],
                "description": "Platform to order from"
            }
        },
        "required": ["order_type", "items"]
    }
    
    def __init__(self, storage, user_id: str, requested_by: str):
        self.storage = storage
        self.user_id = user_id
        self.requested_by = requested_by
    
    def execute(
        self,
        order_type: str,
        items: List[dict],
        platform: Optional[str] = None
    ) -> ToolResult:
        """Create order request"""
        
        try:
            # Convert to OrderItem objects
            order_items = []
            total = 0
            
            for item_data in items:
                order_item = OrderItem(
                    name=item_data["name"],
                    quantity=item_data.get("quantity", 1),
                    unit=item_data.get("unit"),
                    estimated_price=item_data.get("estimated_price")
                )
                order_items.append(order_item)
                if order_item.estimated_price:
                    total += order_item.estimated_price * order_item.quantity
            
            # Create order
            order = Order(
                user_id=self.user_id,
                requested_by=self.requested_by,
                order_type=order_type,
                items=order_items,
                total_amount=total if total > 0 else None,
                platform=platform,
                status=OrderStatus.PENDING
            )
            
            saved = self.storage.create_order(order)
            
            # Format items for message
            item_names = [f"{i.name}" for i in order_items]
            total_str = f" (estimated ₹{int(total)})" if total > 0 else ""
            
            return ToolResult(
                success=True,
                data={
                    "order_id": saved.id,
                    "items": [i.model_dump() for i in order_items],
                    "total": total,
                    "status": "pending"
                },
                message=f"Order request created for {', '.join(item_names)}{total_str}. Waiting for approval."
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
