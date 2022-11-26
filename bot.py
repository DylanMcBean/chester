import disnake, responces
from io import BytesIO


async def send_message(message, user_message):
    try:

        response = responces.handle_responces(message, user_message)
        if type(response) == tuple:
            if response[0] == "image":
                board_image_file = BytesIO()
                response[-1].save(board_image_file,format="PNG")
                board_image_file.seek(0)
                file = disnake.File(board_image_file,filename="image.png")
                await message.channel.send(file=file)
            if response[0] == "image_msg":
                board_image_file = BytesIO()
                response[-1].save(board_image_file,format="PNG")
                board_image_file.seek(0)
                file = disnake.File(board_image_file,filename="image.png")
                await message.channel.send(response[1],file=file)
            if response[0] == "create_thread":
                message = await message.channel.send(response[1])
                thread = await message.channel.create_thread(name="tester",message=message)
                with open(f"games/{message.guild.id}-{thread.id}.temp","wb+") as f:
                    f.write(message.author.id.to_bytes(8,"little"))
                breakpoint
            else:
                await message.channel.send(response)
        else:
            await message.channel.send(response)
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

client = MyClient(intents=disnake.Intents(messages=True,guilds=True,message_content=True,))
with open(".token") as f:
    client.run(f.read())