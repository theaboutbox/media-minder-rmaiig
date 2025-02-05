# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_crewai.ipynb.

# %% auto 0
__all__ = ['SearchTools', 'BrowserTools', 'MediaMinderAgents', 'MediaMinderTasks', 'create_crew']

# %% ../nbs/05_crewai.ipynb 3
import MediaMinder.search as search
import MediaMinder.scrape as scrape
import MediaMinder.html as html

from langchain.tools import tool

# %% ../nbs/05_crewai.ipynb 4
class SearchTools:
    @tool("Search for news articles")
    def search_news(query: str) -> str:
        """Useful to search the web for news about a given topic and return relevant results."""
        results: list[search.SearchResult] = search.run_query(f"!news {query}", page=1)
        text_results = []
        for result in results:
            text_results.append(
                "\n".join(
                    [
                        f"Title: {result.title}",
                        f"URL: {result.url}",
                        f"Snippet: {result.content}",
                        "\n--------------------",
                    ]
                )
            )

        return "\n".join(text_results)

    @tool("Search for content on the web")
    def search_web(query: str) -> str:
        """Useful to search the web for content about a given topic and return relevant results."""
        results: list[search.SearchResult] = search.run_query(query, page=1)
        text_results = []
        for result in results:
            text_results.append(
                "\n".join(
                    [
                        f"Title: {result.title}",
                        f"URL: {result.url}",
                        f"Snippet: {result.content}",
                        "\n--------------------",
                    ]
                )
            )

        return "\n".join(text_results)

# %% ../nbs/05_crewai.ipynb 7
def _html_to_response(html_content: str, max_content_length: int = 4000) -> str:
    article_data: html.Article = html.extract_article(html_content)
    # truncate content if it is too long
    if len(article_data.content) > max_content_length:
        article_data.content = article_data.content[:max_content_length] + "..."
    return "\n".join(
        [
            f"Title: {article_data.metadata['title']}",
            f"Author: {article_data.metadata['author']}",
            f"Date: {article_data.metadata['date']}",
            f"Description: {article_data.metadata['description']}",
            f"Site Name: {article_data.metadata['sitename']}",
            f"URL: {article_data.metadata['url']}",
            "---",
            f"{article_data.content}",
        ]
    )


class BrowserTools:
    @tool("Scrape and extract articles from website content")
    def scrape_website(url: str) -> str:
        """Scrape a website and return the text content."""
        try:
            html_content = scrape.scrape_url(url)
            return _html_to_response(html_content)
        except Exception:
            # Return a stubbed response if the scraping fails
            return "\n".join(
                [
                    f"URL: {url}",
                    "---",
                    "Unable to scrape content from this URL",
                ]
            )

# %% ../nbs/05_crewai.ipynb 10
from crewai import Agent

# %% ../nbs/05_crewai.ipynb 11
class MediaMinderAgents:
    def researcher(self, llm=None):
        return Agent(
            role="Searcher",
            goal="Find news stories mentioning a given company.",
            backstory="""Your job is to find news stories mentioning a given company and pass along the results to the reviewer for review.""",
            verbose=True,
            tools=[SearchTools.search_news],
            llm=llm,
        )
    
    def reviewer(self, llm=None):
        return Agent(
            role="Content Reviewer",
            goal="Review a list of news stories and pick the ones that are relevant.",
            backstory="""Look at the search result summary and eliminate any irrelevant articles. If you cannot tell from the search result summary then accept the article.""",
            verbose=True,
            llm=llm,
        )

    def analyst(self, llm=None):
        return Agent(
            role="Media Analyst",
            goal="Analyze a single news story and extract relevant information about a given company.",
            backstory="""The go-to person for analyzing news stories and extracting relevant information. 
            Your work is crucial for the company's decision-making process. First, ensure the article is really
            written about the given company. Identify all of the companies, products, key events and sentiments 
            mentioned in the article. You are working on a high-priority project for a major client.""",
            verbose=True,
            tools=[BrowserTools.scrape_website],
            llm=llm,
        )

# %% ../nbs/05_crewai.ipynb 13
from crewai import Task

# %% ../nbs/05_crewai.ipynb 14
class MediaMinderTasks:
    def research_news(self, agent, company_name: str) -> Task:
        return Task(
            description=f"Search for news articles about the given company. The customer is interested in recent news about: {company_name}.",
            agent=agent,
            expected_output="A list of articles about the given company, including the title, url and the search result snippet.",
        )
    
    def review_news(self, agent):
        return Task(
            description="Review the search results and eliminate any irrelevant articles. If you cannot tell from the search result summary then accept the article.",
            agent=agent,
            expected_output="A list of articles that are actually about the given company, including the title, url and the search result snippet.",
        )

    def analyze_news(self, agent):
        return Task(
            description="Analyze news articles about the given company and extract the URL, title, companies, products, events, people and sentiments mentioned in each article.",
            agent=agent,
            expected_output="A list containing the URL, title, the companies, products, events, people and sentiments mentioned in each article.",
        )

# %% ../nbs/05_crewai.ipynb 17
from crewai import Crew, Process
from langchain_core.language_models.llms import LLM

# %% ../nbs/05_crewai.ipynb 18
def create_crew(company: str, crew_llm: LLM) -> Crew:
    print("Creating MediaMinder Crew")
    print("  Company:", company)

    researcher = MediaMinderAgents().researcher(llm=crew_llm)
    reviewer = MediaMinderAgents().reviewer(llm=crew_llm)
    analyst = MediaMinderAgents().analyst(llm=crew_llm)

    research_news_task = MediaMinderTasks().research_news(researcher, company)
    review_news_task = MediaMinderTasks().review_news(reviewer)
    analyze_news_task = MediaMinderTasks().analyze_news(analyst)

    return Crew(
        name="MediaMinder Crew",
        agents=[researcher, analyst],
        tasks=[research_news_task, review_news_task, analyze_news_task],
        process=Process.sequential,  # Optional: Sequential task execution is default
        cache=True,
        memory=True,
        max_rpm=50,
        share_crew=True,
        llm=crew_llm,
    )
