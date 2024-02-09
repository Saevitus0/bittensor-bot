import disnake
import bittensor
import asyncio
import threading
from disnake.ext import commands, tasks
#from disnake import Option, OptionType

class BTBot(commands.InteractionBot):
    def __init__(self, intents):
        commands.InteractionBot.__init__(self, intents=intents)    
        self.subtensor = bittensor.subtensor()
        
        self.event_ids = {
            "ServingRateLimitSet",
            "MinDifficultySet",
            "MaxDifficultySet",
            "WeightsVersionKeySet",
            "WeightsSetRateLimitSet",
            "MaxWeightLimitSet",
            "ImmunityPeriodSet",
            "MinAllowedWeightSet",
            "ActivityCutoffSet",
            "RegistrationAllowed",
            "PowRegistrationAllowed",
            "MinBurnSet",
            "MaxBurnSet"
        }
        
        self.subnet_channel_mapping = {
            1: 1161764867166961704,
            2: 1161764868265869314,
            3: 1161764869280903240,
            4: 1161765008347254915,
            5: 1161765035488579635,
            6: 1200530530416988353,
            7: 1162154665971028048,
            8: 1162384774170677318,
            9: 1162768567821930597,
            10: 1163969538191269918,
            11: 1161765231953989712,
            12: 1201941624243109888,
            13: 1185617142914236518,
            14: 1182422353360195695,
            15: 1166816300962693170,
            16: 1166816341697761300,
            17: 1173712344409460766,
            18: 1172669887697653881,
            19: 1186691482749505627,
            20: 1194736998250975332,
            21: 1182096085636878406,
            22: 1189589759065067580,
            23: 1191833510021955695,
            24: 1189234502669697064,
            25: 1174839377659183174,
            26: 1178397855053000845,
            27: 1174835090539433994,
            28: 1176585029367906314,
            29: 1179081290289528864,
            30: 1204855126045753434,
            31: 1179798609273815111,
            #32: 1179081290289528864
        }
        
    async def on_ready(self):
        print(f"{self.user} has activated")
        print(f"In {len(self.guilds)} guilds")
        
        self.check_hyperparameters.start()

    @tasks.loop()
    async def check_hyperparameters(self):
        queue = asyncio.Queue()

        def handle_block_header(obj, update_nr, subscription_id):
            print(f"New block #{obj['header']['number']}")

            block_hash = self.subtensor.get_block_hash(obj['header']['number'])
            events = self.subtensor.substrate.get_events(block_hash)
            for event in events:
                event_dict = event["event"].decode()
                if event_dict["event_id"] in self.event_ids:
                    queue.put_nowait(event_dict)

        # run in a separate thread because of looping, asyncio and subscription working poorly together
        threading.Thread(target=self.subtensor.substrate.subscribe_block_headers, args=(handle_block_header,)).start()

        while True:
            event_dict = await queue.get()
            netuid, value = event_dict["attributes"]
            await self.announce_changes(netuid, event_dict["event_id"], value)
    

    async def announce_changes(self, netuid, hparam, value) :
        print("test")
        for subnet, channel_id in self.subnet_channel_mapping.items():
            if subnet == netuid:
                channel = self.get_channel(channel_id)
                embed = disnake.Embed(
                    title=f"Hyperparameters have been updated.", 
                    color=disnake.Color.yellow(),
                    description=f"{hparam} for subnet {subnet} has updated to: {value}.",
                    timestamp=disnake.utils.utcnow()
                )
                
                await channel.send(embed=embed)
                
    # havent tested this properly yet
    @commands.slash_command(name="list_hyperparams", description="Lists the current hyperparameters")
    async def cmd(self, ctx: disnake.ApplicationCommandInteraction):
        #hyperparameters = bittensor.subtensor.get_subnet_hyperparameters()
        #print(list(self.subnet_channel_mapping.keys())[list(self.subnet_channel_mapping.values()).index(inter.channel.id)])
        
        await ctx.response.send_message(f'Current hyperparameters: {list(self.subnet_channel_mapping.keys())[list(self.subnet_channel_mapping.values()).index(ctx.channel.id)]}')


if __name__ == "__main__":
    intents = disnake.Intents.all()
    intents.message_content = True
    
    bot = BTBot(intents)
    bot.run("TOKEN HERE")
    #bot.loop.create_task(bot.check_hyperparameters())