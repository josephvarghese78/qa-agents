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
import authorize as ae

GITHUB_TOKEN = ae.get_token()



async def ask_copilot_with_attachments(prompt, attachments, model = None) -> str:
    """
    Reusable engine that accepts a prompt and a list of file attachments,
    parses them into context, and returns the Copilot response using the SDK.
    """

    # 2. Construct the final comprehensive payload
    #final_prompt = prompt
    #if attachments:
    #    final_prompt = f"Context from attachments:\n{attachments}\n\nUser Question:\n{prompt}"

    response_content = []

    #print(final_prompt)
    #print("")

    # 3. Spin up the Copilot SDK Client and Session via async context managers
    async with CopilotClient() as client:
        session_args = {
        "on_permission_request":PermissionHandler.approve_all,
        "system_message":{
            "content": """
                    You are a text-only assistant. 
                    Never attempt to use tools to write files, or modify files, 
                    but you can read and analyze the content of attached files to answer questions and generate outputs.
                    Return all generated content directly in the response.
            """
        },
        "github_token":GITHUB_TOKEN
        }

        if model:
            session_args["model"] = model


        async with await client.create_session(**session_args) as session:

            # Setup an event handler to collect stream outputs
            done = asyncio.Event()

            def on_event(event):
                # Check for incoming assistant message variations based on SDK spec
                print(event)
                if isinstance(event.data, AssistantMessageData):
                    content = getattr(event.data, "content", "")
                    if content:
                        print(content)
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





