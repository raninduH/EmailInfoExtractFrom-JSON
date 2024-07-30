import json
import os

def split_json_file(input_file, output_dir, chunk_size=200):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        total_docs = len(data)
        num_chunks = (total_docs + chunk_size - 1) // chunk_size  # Calculate number of chunks
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total_docs)
            chunk = data[start_idx:end_idx]
            
            output_filename = os.path.join(output_dir, f'chunk_{i + 1}.json')
            with open(output_filename, 'w', encoding='utf-8') as out_file:
                json.dump(chunk, out_file, ensure_ascii=False, indent=4)

            print(f'chunk {i + 1} written to {output_filename}')

# Example usage
input_file = r"main_chunks\a0_11.json"  # Replace with your input JSON file path
output_directory = r'a0_11_chunks'  # Replace with your desired output directory path
split_json_file(input_file, output_directory, chunk_size=25)