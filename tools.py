from fastmcp import FastMCP
from scraper import setup_driver,parse_results,fetch_page
from langgraph.graph import StateGraph, MessagesState, START, END
from pydantic import BaseModel,Field

mcp = FastMCP("Mcp-on-air")

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
 
 
class AnsibleCheck(BaseModel):
    is_ansible_related: bool = Field(
        description="True if the content is related to Ansible automation platform, playbooks, roles, modules, or ansible ecosystem"
    )
 
 
# Load Ollama model
llm = ChatOllama(
    model="tinyllama:latest",
    temperature=0
)
 
# Enforce structured output
structured_llm = llm.with_structured_output(AnsibleCheck)
 
 
prompt = ChatPromptTemplate.from_template(
"""
You are a strict domain classifier.
 
Determine whether the following text is related to Ansible automation.
 
Consider topics such as:
- Ansible playbooks
- Ansible roles
- Ansible modules
- Ansible Tower / AWX
- Infrastructure automation using Ansible
- ansible.cfg, YAML playbooks, inventory
 
If the topic is unrelated (AWS, Terraform, Kubernetes, etc.) return false.
 
Text:
{text}
"""
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
        driver = setup_driver()
        search_terms = [query]

        for term in search_terms:
            print(f"Scraping: '{term}'...")

            results = parse_results(fetch_page(driver, term), term)
            if results:
                all_results.extend(results)
                print(f"→ Captured {len(results)} results")

        # Process the results with the classifier chain
        chain_output = classifier_chain.invoke({"text": all_results})
        print(chain_output.is_ansible_related)
        # Ensure proper structure and check for Ansible relevance
        if not chain_output.is_ansible_related:
            all_results = []

    except Exception as e:
        print(f"Error: {e}")
        return ["the server is facing some issues. The team is trying to solve it ASAP."]

    finally:
        # Ensuring the driver is closed
        if 'driver' in locals():
            driver.quit()

    return all_results



