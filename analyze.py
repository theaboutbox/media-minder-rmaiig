import sys
import MediaMinder.crewai as agents
from langchain_openai import ChatOpenAI

# Get the company name from the command line
company = sys.argv[1]

llm = ChatOpenAI(model="gpt-4o")

# Create a crewai agent
crew = agents.create_crew(company, llm)
crew.kickoff()
