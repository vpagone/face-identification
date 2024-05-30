import yaml

def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        return config

if __name__ == "__main__":
    config_path = 'config.yaml'
    config = load_yaml_config(config_path)
       
    local_sources = config.get('local_sources', [])
    for local_source in local_sources:
        name = local_source.get('name', 'Unnamed')
        print(f"Local Source: {name}")
        webcams = local_source.get('webcams', [])
        for webcam in webcams:
            print(f"  Webcam Name: {webcam['webcam_name']}, Webcam Number: {webcam['webcam_number']}")
            
        video_files = local_source.get('video_files', [])
        for video_file in video_files:
            print(f"  Video File Name: {video_file['video_name']}, Webcam Number: {video_file['location']}")
            
    remote_sources = config.get('network_sources', [])
    for remote_source in remote_sources:
        name = remote_source.get('name', 'Unnamed')
        print(f"Remore Source: {name}")
        webcams = remote_source.get('webcams', [])
        for webcam in webcams:
            print(f"  Webcam Name: {webcam['webcam_name']}, Webcam IP: {webcam['webcam_ip']}")
    
