from tools import mcp 

def main():
    mcp.run(transport="sse", port=8000,host="0.0.0.0")

if __name__ == "__main__":
    
    main()
