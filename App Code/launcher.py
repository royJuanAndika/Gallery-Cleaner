import sys
import traceback
import os

def main():
    try:
        # Import and run the main application only after setting up error handling
        from gallery_cleaner_gui import main as run_app
        run_app()
    except Exception as e:
        # Get the full error traceback
        error_msg = f"ERROR: {str(e)}\n\n{traceback.format_exc()}"
        
        # Write to a log file
        with open("error_log.txt", "w") as f:
            f.write(error_msg)
        
        # Also show in console
        print(error_msg)
        
        # Keep console open
        input("\nPress Enter to exit...")
        
        sys.exit(1)

if __name__ == "__main__":
    main()