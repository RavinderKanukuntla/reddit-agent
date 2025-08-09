from nlip_sdk.nlip import (
    NLIP_Message,
    NLIP_Factory
)
from multiprocessing import get_logger
import logging

from nlip_server import server
from nlip_sdk import nlip
from reddit_search.mcp_client import MCPClient

logger = logging.getLogger('uvicorn.error')

class ChatApplication(server.NLIP_Application):
    async def startup(self):
        logger.info("Starting app...")

    async def shutdown(self):
        return None

    async def create_session(self) -> server.NLIP_Session:
        return ChatSession(MCPClient())


class ChatSession(server.NLIP_Session):

    def __init__(self, client: MCPClient):
        self.client = client

    async def start(self):
        try:
            logger.info(f"Connecting to the MCP server...")
            await self.client.connect_to_server(
                "reddit_search/mcp_server.py"
            )
            logger.info(f"Connected.")
        except Exception as e:
            logger.info(f"Error connecting MCP server {e}")
            await self.client.cleanup()

    async def execute(
        self, msg: NLIP_Message) -> NLIP_Message:
        logger = self.get_logger()
        #text = msg.extract_text()
        text = msg.content
        print(f"question: {msg.content}")
        logger.info(f"Input text. {text}")
        

        try:
            response = await self.client.process_channels(msg.content)
            logger.info(f"Response : {response}")
            msg.content = response
            return msg
        except Exception as e:
            logger.error(f"Exception {e}")
            return None

    async def stop(self):
        logger.info(f"Stopping chat session")
        await self.client.cleanup()
        self.server = None


app = server.setup_server(ChatApplication())
