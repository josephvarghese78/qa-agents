import asyncio
import os
#from docx import Document
from copilot import CopilotClient
from copilot.session_events import AssistantMessageData
from copilot.session import PermissionHandler
from copilot.session_events import (
    AssistantMessageData,
    AssistantReasoningData,
    ToolExecutionStartData,
    SessionIdleData
)
import random
import time


class CopilotAssistant:
    def __init__(self, agent, token=None, model = None):
        self.agent = agent
        self.token = token
        self.model = model
        self.session_args = {
        "on_permission_request":PermissionHandler.approve_all,
        "system_message":{
            "content": """
                    You are a text-only assistant. 
                    Never attempt to use tools to write files, or modify files, 
                    but you can read and analyze the content of attached files to answer questions and generate outputs.
                    Return all generated content directly in the response.
            """
        },
        "github_token":token
        }

    async def ask(self, prompt, attachments=None):
        t=random.randint(1,20)
        print('*'*50)
        print(f"Simulating agent '{self.agent}' thinking for {t} seconds...")
        time.sleep(t)
        print('*' * 50)
        return f"passed! response from {self.agent}"

    async def ask1(self, prompt, attachments):
        """
        Reusable engine that accepts a prompt and a list of file attachments,
        parses them into context, and returns the Copilot response using the SDK.
        """

        response_content = []
        session_log = []

        # 3. Spin up the Copilot SDK Client and Session via async context managers
        async with CopilotClient() as client:

            if self.model:
                self.session_args["model"] = self.model


            async with await client.create_session(**self.session_args) as session:

                # Setup an event handler to collect stream outputs
                done = asyncio.Event()

                def on_event(event):
                    # Check for incoming assistant message variations based on SDK spec
                    print(event)
                    session_log.append(event)
                    if isinstance(event.data, AssistantMessageData):
                        content = getattr(event.data, "content", "")
                        if content:
                            #print(content)
                            response_content.append(content)
                    #elif hasattr(event.data, "type") and event.data.type == "session.idle":
                    elif isinstance(event.data, SessionIdleData):
                        done.set()

                # Subscribe to the session event loop
                session.on(on_event)

                # Send prompt down the pipeline
                if attachments:
                    await session.send(prompt, attachments=attachments)
                else:
                    await session.send(prompt)

                # Keep execution block open until the model stops streaming
                await done.wait()

        return "".join(response_content)





