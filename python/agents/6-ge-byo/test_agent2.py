import asyncio
from ge_byo.agent import root_agent

async def main():
    print(dir(root_agent))
    
if __name__ == '__main__':
    asyncio.run(main())
