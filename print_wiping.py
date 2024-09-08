import os

target_wiped_file_path = r"C:\Users\hj021\Desktop\안티포렌식\개발\final\$J.copy0"
excel_signature = bytes.fromhex("78 00 6C 00 73 00 78 00")  # x.l.s.x
j_record_signature = bytes.fromhex("00 00 02 00 00 00")
CHUNK_SIZE = 4096  # Adjust the chunk size as needed

def detect_wiped(file_path):
    if not os.path.isfile(file_path):
        return f"{file_path}, File not found"
        
    wiped_checker = False
    file_offset = 0
    
    wiping_trace = []
    
    with open(file_path, "rb") as file:
        while True:
            file.seek(file_offset)
            chunk = file.read(CHUNK_SIZE)
            
            # Check for the first occurrence of the Excel signature in the current chunk
            excel_index = chunk.find(excel_signature)
            while excel_index != -1:
                # Search for the closest preceding J record signature before the Excel signature
                j_search_chunk = chunk[:excel_index]
                j_record_index = j_search_chunk.rfind(j_record_signature)
                if j_record_index != -1:
                    closest_j_record_signature_offset = file_offset + j_record_index
                else:
                    closest_j_record_signature_offset = -1

                # Check if we found a valid J record before the Excel signature
                if closest_j_record_signature_offset != -1:
                    # Process the found J record
                    file.seek(closest_j_record_signature_offset)  # Move past the size field
                    if file.read(len(j_record_signature)) == j_record_signature:
                        # Check for the same Excel signature in the next log record
                        file.seek(-8, 1)
                        log_record_size = int.from_bytes(file.read(2), byteorder='little')
                        file.seek(log_record_size, 1)
                       
                        file.seek(-2,1)
                        next_chunk_log_record_size = int.from_bytes(file.read(2), byteorder='little')
                        
                        if (next_chunk_log_record_size != log_record_size):
                            excel_index = chunk.find(excel_signature, excel_index + len(excel_signature))
                            continue
                        
                        file.seek(-2, 1)
                        next_chunk = file.read(log_record_size)
                        if excel_signature in next_chunk:
                            pass
                        else:
                            wiping_trace.append("와이핑 흔적 발견")
                            wiped_checker = True
                            break  # Exit inner loop if wiped condition is confirmed
                    else:
                        wiping_trace.append("Invalid J record signature found")
                
                # Look for the next occurrence of Excel signature in the same chunk
                excel_index = chunk.find(excel_signature, excel_index + len(excel_signature))

            # Exit outer loop if wiped condition is confirmed or end of file is reached
            if wiped_checker or len(chunk) < CHUNK_SIZE:
                break
            
            # Move to the next chunk
            file_offset += CHUNK_SIZE

        # Check if wiped_checker is False after processing
        if not wiped_checker:
            wiping_trace.append("File does not appear to be wiped.")
            
    return f"{file_path}, {'; '.join(wiping_trace)}"

def main():
    result = detect_wiped(target_wiped_file_path)
    print(result)

if __name__ == "__main__":
    main()


