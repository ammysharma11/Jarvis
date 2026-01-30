# 🏠 Jarvis - AI Home Assistant for Alexa

An intelligent family home assistant powered by GPT-4 with persistent memory. Jarvis learns about your family, remembers preferences, and gets smarter with every conversation.

## ✨ Features

- **Natural Conversations**: Talk to Jarvis like a family member
- **Persistent Memory**: Remembers facts and preferences across sessions
- **Multi-Tool Support**: Weather, reminders, grocery lists, calculations
- **Family-Focused**: Different modes for adults, children, and elderly
- **Order Management**: Request groceries/medicines with approval workflow

## 🚀 Quick Setup

### Prerequisites

1. **Amazon Developer Account** - [developer.amazon.com](https://developer.amazon.com)
2. **Supabase Account** (Free) - [supabase.com](https://supabase.com)
3. **OpenAI API Key** - [platform.openai.com](https://platform.openai.com)
4. **OpenWeather API Key** (Optional) - [openweathermap.org](https://openweathermap.org/api)

### Step 1: Setup Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor**
3. Copy contents of `supabase-schema.sql` and run it
4. Go to **Settings → API** and copy:
   - Project URL → `SUPABASE_URL`
   - `anon` public key → `SUPABASE_KEY`

### Step 2: Create Alexa Skill

1. Go to [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Click **Create Skill**
3. Configure:
   - **Name**: Smart Home Jarvis
   - **Locale**: English (IN) or your preferred
   - **Model**: Custom
   - **Hosting**: Alexa-hosted (Python)
4. Select **Start from Scratch** template
5. Click **Create Skill** and wait

### Step 3: Import Code

**Option A: Import from GitHub** (Recommended)
1. Push this repo to your GitHub
2. In Alexa Console, click **Import Skill** and paste your repo URL

**Option B: Manual Upload**
1. Go to **Code** tab in Alexa Console
2. Create the folder structure and paste each file

### Step 4: Set Environment Variables

In Alexa Developer Console:
1. Go to **Code** tab
2. Click on **requirements.txt** and ensure dependencies are listed
3. For environment variables, you'll need to add them in your Lambda

**Important**: Alexa-hosted skills don't have a direct way to set env vars. 
You can either:
- Hardcode values in `agent/config.py` (for testing only)
- Use AWS Secrets Manager (advanced)

For testing, edit `lambda/agent/config.py`:
```python
self.openai_api_key = "sk-your-key-here"
self.supabase_url = "https://xxx.supabase.co"
self.supabase_key = "eyJ..."
```

### Step 5: Build & Deploy

1. Go to **Build** tab
2. Click **Build Skill** (takes ~1 minute)
3. Go to **Code** tab
4. Click **Deploy** button

### Step 6: Test

1. Go to **Test** tab
2. Enable skill testing: "Development"
3. Type or say: **"open jarvis"**
4. Try: "What's the weather in Mumbai?"

## 📁 Project Structure

```
jarvis-alexa-skill/
├── lambda/
│   ├── lambda_function.py      # Alexa handler
│   ├── requirements.txt        # Dependencies
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings & API keys
│   │   ├── core.py             # Main AI agent
│   │   └── prompts.py          # System prompts
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── models.py           # Data models
│   │   ├── short_term.py       # Conversation memory
│   │   ├── long_term.py        # Persistent memory
│   │   └── extractor.py        # Learn from conversations
│   ├── tools/
│   │   ├── __init__.py         # Tool registry
│   │   ├── base.py             # Base tool class
│   │   ├── weather.py          # Weather lookup
│   │   ├── calculator.py       # Math calculations
│   │   ├── time_tool.py        # Current time
│   │   ├── reminders.py        # Set/get reminders
│   │   └── grocery.py          # Grocery list management
│   └── storage/
│       ├── __init__.py
│       └── supabase_client.py  # Database operations
├── skill-package/
│   ├── skill.json              # Skill manifest
│   └── interactionModels/
│       └── custom/
│           ├── en-US.json      # US English model
│           └── en-IN.json      # India English model
├── supabase-schema.sql         # Database setup
└── README.md
```

## 🛠️ Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `get_weather` | Get weather for a city | "What's the weather in Delhi?" |
| `calculator` | Math calculations | "What's 15% of 200?" |
| `get_current_time` | Get current time | "What time is it?" |
| `set_reminder` | Set a reminder | "Remind me to call mom at 5pm" |
| `get_reminders` | View reminders | "What are my reminders?" |
| `add_to_grocery_list` | Add grocery items | "Add milk and eggs to my list" |
| `view_grocery_list` | View grocery list | "What's on my grocery list?" |
| `create_order_request` | Request an order | "Order tomatoes from Zepto" |

## 💬 Example Conversations

```
You: "Alexa, open Jarvis"
Jarvis: "Hi! I'm Jarvis. How can I help you today?"

You: "What's the weather in Bangalore?"
Jarvis: "It's 28 degrees and partly cloudy in Bangalore."

You: "Add tomatoes, onions, and milk to my grocery list"
Jarvis: "Added 3 items to your grocery list: tomatoes, onions, milk."

You: "Remind me to take my medicine at 8pm"
Jarvis: "Reminder set for 8:00 PM: take your medicine"

You: "My son loves chocolate cake"
Jarvis: "That's sweet! I'll remember that about your son."
[Later...]
You: "What should I get for my son's birthday?"
Jarvis: "Since your son loves chocolate cake, how about ordering one?"
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon key |
| `OPENWEATHER_API_KEY` | No | For weather feature |
| `OPENAI_MODEL` | No | Default: gpt-4o |

### Customization

**Change invocation name**: Edit `skill-package/interactionModels/custom/*.json`
```json
"invocationName": "jarvis"  // Change to your preferred name
```

**Adjust response length**: Edit `lambda/agent/config.py`
```python
self.max_response_length = 300  # Characters for voice
```

## 📊 Database Tables

- `users` - User profiles and permissions
- `facts` - Learned facts about users
- `preferences` - User preferences
- `conversations` - Conversation history
- `messages` - Individual messages
- `orders` - Order requests
- `reminders` - Scheduled reminders
- `grocery_list` - Shopping list items

## 🔒 Security Notes

- Never commit API keys to GitHub
- Use environment variables or secrets management
- Supabase Row Level Security is enabled
- For production, restrict API key permissions

## 🐛 Troubleshooting

**"I had trouble thinking about that"**
- Check OpenAI API key is valid
- Check you have API credits

**"Weather API not configured"**
- Add OPENWEATHER_API_KEY

**Database errors**
- Verify Supabase URL and key
- Check if schema is created

**Skill not responding**
- Check CloudWatch logs in AWS Console
- Ensure skill is deployed

## 📈 Future Improvements

- [ ] WhatsApp approval notifications
- [ ] Voice user identification
- [ ] Smart home device control
- [ ] Recipe suggestions
- [ ] Calendar integration
- [ ] Multi-language support

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Credits

Built with:
- [OpenAI GPT-4](https://openai.com)
- [Supabase](https://supabase.com)
- [Alexa Skills Kit](https://developer.amazon.com/alexa)
- [Pydantic](https://pydantic-docs.helpmanual.io)
