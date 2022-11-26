import disnake, responces


async def send_message(message, user_message):
    try:
        responce = responces.handle_responces(message, user_message)
        if type(responce) == tuple:
            if responce[0] == "image":
                with open(f"{message.guild.id}-{message.channel.id}.png","rb") as f:
                    picture = disnake.File(f)
                    await message.channel.send(file=picture)
            if responce[0] == "image_msg":
                with open(f"{message.guild.id}-{message.channel.id}.png","rb") as f:
                    picture = disnake.File(f)
                    await message.channel.send(responce[1],file=picture)
        else:
            await message.channel.send(responce)
    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send(f"Error: {e}")


class MyClient(disnake.Client):
        async def on_ready(self):
            print(f"{self.user} is now running")

        async def on_message(self,message):
            if message.author == client.user:
                return # make sure bot cannot communicate with itsself
        
            user_message = str(message.content)

            if user_message.startswith("chester"):
                user_message = user_message[8:]
            else:
                return None

            await send_message(message, user_message)

client = MyClient(intents=disnake.Intents(messages=True,guilds=True,message_content=True))
with open(".token") as f:
    client.run(f.read())