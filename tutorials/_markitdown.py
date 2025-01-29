import os
import argparse
from markitdown import MarkItDown
from openai import OpenAI


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=str)
    parser.add_argument("output_path", type=str)
    return parser.parse_args()


def main():
    args = parse_args()
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    md = MarkItDown(llm_client=client, llm_model="gpt-4o-mini")
    result = md.convert(args.input_path)
    with open(args.output_path, "w") as f:
        f.write(result.text_content)


if __name__ == "__main__":
    main()
