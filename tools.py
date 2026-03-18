from fastmcp import FastMCP
from scraper import setup_driver,parse_results,fetch_page
from langgraph.graph import StateGraph, MessagesState, START, END
from pydantic import BaseModel,Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from ddgs import DDGS
from scraper_docs_trif import scrape_url


mcp = FastMCP("Mcp-on-air")


class AnsibleCheck(BaseModel):
    is_ansible_related: bool = Field(
        description="True ONLY if the text is primarily about Ansible; otherwise false."
    )


llm = ChatOllama(model="gemma3:1b-it-qat", temperature=0)
structured_llm = llm.with_structured_output(AnsibleCheck)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a strict domain classifier for Ansible.\n"
            "Return ONLY a JSON object with the single key: is_ansible_related.\n"
            "If you are unsure, return false.\n"
            "Do NOT explain your reasoning.\n",
        ),

        ("human", "Text: Write an Ansible playbook to install nginx and start the service on Ubuntu."),
        ("assistant", '{{"is_ansible_related": true}}'),

        ("human", "Text: Create a Kubernetes Deployment YAML for nginx with 3 replicas."),
        ("assistant", '{{"is_ansible_related": false}}'),

        ("human", "Text:\n{text}"),
    ]
)

classifier_chain = prompt | structured_llm
# @mcp.tool
# def get_relevant_data(query: str)->list:
#     """Run scraper to get relevant data based on the query."""
    
#     all_results = []

#     try:
#         driver = setup_driver()

#         search_terms = [query] 

#         for term in search_terms:
#             print(f"Scraping: '{term}'...")

#             results = parse_results(fetch_page(driver, term), term)
#             if results:
                
#                 all_results.extend(results)
#                 print(f"→ Captured {len(results)} results")

#         chain_output=classifier_chain.invoke({"text":all_results})
#         if not chain_output.is_ansible_related:
#             all_results=[]

#     except Exception as e:
#         return all_results.append("the server is facing some issues.The team is trying to solve it asap.")       
            

#     finally:
#         # ensuring driver is closed
#         if 'driver' in locals():
#             driver.quit()



#     return all_results  



@mcp.tool
def get_relevant_data(query: str) -> list:
    """Run scraper to get relevant data based on the query."""

    all_results = []

    try:
        # driver = setup_driver()
        search_terms = [query]

        for term in search_terms:
            print(f"Scraping: '{term}'...")

            # results = parse_results(fetch_page(driver, term), term)
            urls_dict = DDGS().text(query, max_results=5)
            urls=[u["href"]for u in urls_dict]
            for u in urls:
                result=scrape_url(u)
                all_results.extend(result)
                print(f"→ Captured {len(result)} results")

        # Process the results with the classifier chain
        # chain_output = classifier_chain.invoke({"text": all_results})
        # print(chain_output.is_ansible_related)
        # # Ensure proper structure and check for Ansible relevance
        # if not chain_output.is_ansible_related:
        #     all_results = []

    except Exception as e:
        print(f"Error: {e}")
        return ["the server is facing some issues. The team is trying to solve it ASAP."]

    # finally:
    #     # Ensuring the driver is closed
    #     if 'driver' in locals():
    #         driver.quit()

    return all_results



