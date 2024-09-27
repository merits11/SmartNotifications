import argparse
import logging

from llm.client import get_llm_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [PID:%(process)d][%(threadName)s] - %(message)s",
)


def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="CLI tool for processing input strings.")

    # Add an argument for the action
    parser.add_argument('--action', type=str, help='Natural language instructions to process')

    # Parse the arguments
    args = parser.parse_args()

    # Implement your logic based on the action argument
    if args.action:
        logging.info(f"Processing action: {args.action}")
        process_action(args)
    else:
        logging.warning("No action provided.")


def process_action(args):
    action = args.action
    client = get_llm_client()
    response = client.get_chat_completion(
        [{"role": "system", "content": "You are a helpful assistant to automate engineer daily jobs on Mac OS."},
         {"role": "user", "content": action}, ])
    logging.info(response)


if __name__ == "__main__":
    main()
