![Image](https://graph.org/file/9901c2070cea11d1aa194.jpg)

## WaifuXGrab


![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)<br> [![Open Source Love svg2](https://badges.frapsoft.com/os/v2/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)<br>

[![Source](https://img.shields.io/badge/Source-SenpaiLabs%2FWaifuXGrab-blue)](https://github.com/SenpaiLabs/WaifuXGrab)

## About The Repository
WaifuXGrab is an open-source character catcher bot for Telegram.
- For Example, Grab/Hunt/Protecc/Collect etc.. These Types of Bot You must have seen it on your telegram groups..
- This bot sends characters in group after every 100 Messages Of Groups Then any user can Guess that character's Name Using /guess Command.

- The bot is built with Python-Telegram-Bot v20.6, Pyrogram, MongoDB, and Imgbb image hosting.

## HOW TO UPLOAD CHARACTERS?

Format:
```
/upload img_url character-name anime-name rarity-number
```
#### Example:
```
/upload Img_url muzan-kibutsuji Demon-slayer 3
```



use Rarity Number accordingly rarity Map

| Number | Rarity     |
| ------ | -----------|
| 1 | ⚪️ Common   |
| 2 | 🟣 Rare     |
| 3 | 🟡 Legendary|
| 4 | 🟢 Medium   |


## USER COMMANDS
- `/guess` - Guess the character
- `/fav` - Add a character to favorites
- `/trade` - Trade a character with another user
- `/gift` - Gift a character to another user
- `/collection` - Boast your harem collection
- `/topgroups` - List the groups with biggest harem (globally)
- `/top` - List the users with biggest harem (globally)
- `/ctop` - List the users with biggest harem (current chat)
- `/changetime` - Change the frequency of character spawn

## SUDO USER COMMANDS..
- `/upload` - Add a new character to the database
- `/delete` - Delete a character from the database
- `/update` - Update stats of a character in the database
- `/ping` - Pings the bot and sends a response
- `/stats` - Lists number of groups and users
- `/list` - Sends a document with list of all users that used the bot
- `/groups` - Sends a document with list of all groups that the bot has been in

## OWNER COMMANDS
- `/broadcast` - Broadcast a replied message to bot users and groups
- `/addsudo` - Add a sudo user permanently in MongoDB
- `/rmsudo` - Remove a sudo user from MongoDB
- `/sudolist` - Show owner and sudo users. Everyone can use this command.

## DEPLOYMENT METHODS

### Docker Deploy
- Clone the repository and enter the project folder:
```bash
git clone https://github.com/SenpaiLabs/WaifuXGrab
cd WaifuXGrab
```

- Create your environment file:
```bash
cp .env.example .env
```

- Fill these required values in `.env`:
```env
API_ID=
API_HASH=
BOT_TOKEN=
MONGO_URL=
IMGBB_API_KEY=
OWNER_ID=
CHARA_CHANNEL_ID=
```

- Build the Docker image:
```bash
docker build -t waifuxgrab .
```

- Start the bot:
```bash
docker run -d --name waifuxgrab --env-file .env --restart unless-stopped waifuxgrab
```

- Check logs:
```bash
docker logs -f waifuxgrab
```

- Stop or restart:
```bash
docker stop waifuxgrab
docker restart waifuxgrab
```

### Heroku
- Fork The Repository
- Add the required environment variables from [`.env.example`](./.env.example)
- Deploy your forked repository

### Local Deploy/VPS
- Create `.env` from [`.env.example`](./.env.example) and fill the required values
- Open your VPS terminal (we're using Debian based) and run the following:
```bash
sudo apt-get update && sudo apt-get upgrade -y

sudo apt-get install python3-pip -y
sudo pip3 install -U pip

git clone https://github.com/SenpaiLabs/WaifuXGrab && cd WaifuXGrab

pip3 install -U -r requirements.txt

sudo apt install tmux && tmux
python3 main.py
```

## License
The Source is licensed under MIT, and hence comes with no Warranty whatsoever.

## Appreciation
If you appreciate this Code, make sure to star ✨ the repository.

## Developer Suggestions
- Don't Use heroku. Deploy on Heroku is just for testing. Otherwise Bot's Inline will Work Too Slow.
- Use a reliable VPS provider
