from langgraph.graph.state import CompiledGraph  # Import the CompiledGraph class from langgraph
from langchain_core.runnables.graph import MermaidDrawMethod  # Import the drawing method enum


def save_graph_as_png(app: CompiledGraph, output_file_path) -> None:
    """
    Saves a visualization of the LangGraph workflow as a PNG image file.
    
    This function takes a compiled LangGraph application and exports a visual 
    representation of its workflow structure to a PNG file. The visualization 
    is created using the Mermaid diagram format and shows how different analyst
    agents are connected in the processing pipeline.
    
    From a financial perspective, this is similar to visualizing the structure of a 
    complex financial model or analysis workflow, showing how different components
    (like DCF, comparable analysis, etc.) connect and feed into each other.
    
    Args:
        app (CompiledGraph): The compiled LangGraph application to visualize.
                            This contains the workflow structure with all nodes and edges.
        
        output_file_path (str): The file path where the PNG image should be saved.
                               If an empty string is provided, defaults to "graph.png".
    
    Returns:
        None: The function writes the PNG file to disk but doesn't return anything.
    
    Example usage:
        save_graph_as_png(my_analyst_graph, "analyst_workflow.png")
    """
    # Generate the PNG image data using Mermaid's API
    # This converts the graph structure into a visual diagram
    png_image = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)
    
    # Determine the output file path - use the provided path or default to "graph.png"
    file_path = output_file_path if len(output_file_path) > 0 else "graph.png"
    
    # Write the binary PNG data to the specified file
    with open(file_path, "wb") as f:
        f.write(png_image)