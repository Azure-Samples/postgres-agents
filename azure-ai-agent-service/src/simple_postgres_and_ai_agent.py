# %%
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet
from datetime import datetime
from legal_agent_tools import user_functions # user functions which can be found in a legal_agent_tools.py file.
from dotenv import load_dotenv
# Load environment variables
load_dotenv("../.env")

# Create an Azure AI Client from a connection string, copied from your Azure AI Foundry project.
# It should be in the format "<HostName>;<AzureSubscriptionId>;<ResourceGroup>;<HubName>"
# Customers need to login to Azure subscription via Azure CLI and set the environment variables
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ["PROJECT_CONNECTION_STRING"],
)

# Initialize agent toolset with user functions
functions = FunctionTool(user_functions)
toolset = ToolSet()
toolset.add(functions)

agent = project_client.agents.create_agent(
    model= os.environ["MODEL_DEPLOYMENT_NAME"], 
    name=f"legal-cases-agent-{datetime.now().strftime('%Y%m%d%H%M')}",
    description="Legal Cases Agent", 
    instructions=f"""
    You are a helpful legal assistant that can retrieve information about legal cases. 
    The current date is {datetime.now().strftime('%Y-%m-%d')}.
    """, 
    toolset=toolset
)
print(f"Created agent, ID: {agent.id}")

# %%
# Create thread for communication
thread = project_client.agents.create_thread()
print(f"Created thread, ID: {thread.id}")

# Create message to thread
message = project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="Water leaking into the apartment from the floor above, What are the prominent legal precedents in Washington on this problem in the last 10 years?"
)
print(f"Created message, ID: {message.id}")


# %%
from pprint import pprint

# Create and process agent run in thread with tools
run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
print(f"Run finished with status: {run.status}")

if run.status == "failed":
    print(f"Run failed: {run.last_error}")

# Fetch and log all messages
messages = project_client.agents.list_messages(thread_id=thread.id)
print(f"Messages: {messages}")
pprint(messages['data'][0]['content'][0]['text']['value'])


# %%
#Delete the agent when done
# project_client.agents.delete_agent(agent.id)
# print("Deleted agent")


