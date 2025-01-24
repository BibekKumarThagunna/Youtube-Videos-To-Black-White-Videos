import os
import streamlit as st
from moviepy.editor import VideoFileClip, vfx
import uuid
import yt_dlp

def get_video_info(url):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def get_resolutions(info):
    resolutions = set()
    for f in info['formats']:
        if f.get('vcodec') != 'none':
            if f.get('height'):
                resolutions.add(f['height'])
            elif f.get('quality_label'):  # For some live streams
                resolutions.add(int(f['quality_label'].split('p')[0]))
    return sorted(resolutions, reverse=True)

def main():
    st.title("YouTube to B&W Converter (yt-dlp)")
    
    if not os.path.exists("temp"):
        os.makedirs("temp")

    url = st.text_input("Enter YouTube URL:")

    if 'resolutions' not in st.session_state:
        st.session_state.resolutions = None
    if 'processed_path' not in st.session_state:
        st.session_state.processed_path = None

    if st.button("Fetch Available Qualities"):
        try:
            info = get_video_info(url)
            st.session_state.resolutions = get_resolutions(info)
            st.session_state.video_info = info
        except Exception as e:
            st.error(f"Error fetching video: {str(e)}")

    if st.session_state.resolutions:
        selected_res = st.selectbox("Select Video Resolution", st.session_state.resolutions)

        if st.button("Convert to Black & White"):
            try:
                temp_id = uuid.uuid4()
                download_path = os.path.join("temp", f"temp_{temp_id}.mp4")

                # Format selection for video+audio or video-only + audio
                ydl_opts = {
                    'format': f'bestvideo[height={selected_res}]+bestaudio/best[height={selected_res}]',
                    'outtmpl': os.path.join("temp", f"temp_{temp_id}"),
                    'merge_output_format': 'mp4',
                    'quiet': True,
                    'no_warnings': True,
                }

                with st.spinner("Downloading and processing video..."):
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                    # If separate streams were downloaded, merge them
                    temp_video = os.path.join("temp", f"temp_{temp_id}.f*")
                    if not os.path.exists(download_path):
                        os.rename(temp_video, download_path)

                # Process video
                with st.spinner("Converting to black and white..."):
                    video = VideoFileClip(download_path)
                    bw_video = video.fx(vfx.blackwhite)
                    
                    processed_filename = f"bw_{temp_id}.mp4"
                    processed_path = os.path.join("temp", processed_filename)
                    
                    bw_video.write_videofile(processed_path, codec='libx264', threads=4)
                    
                    video.close()
                    bw_video.close()
                    
                    st.session_state.processed_path = processed_path
                    os.remove(download_path)
                    
                st.success("Conversion completed!")
            except Exception as e:
                st.error(f"Error processing video: {str(e)}")

    if st.session_state.processed_path is not None:
        try:
            file_size = os.path.getsize(st.session_state.processed_path) / (1024 * 1024)
            st.write(f"File size: {file_size:.2f} MB")

            with open(st.session_state.processed_path, "rb") as f:
                st.download_button(
                    label="Download Black & White Video",
                    data=f,
                    file_name="bw_video.mp4",
                    mime="video/mp4"
                )
            
            os.remove(st.session_state.processed_path)
            st.session_state.processed_path = None
            
        except Exception as e:
            st.error(f"Error handling file: {str(e)}")

if __name__ == "__main__":
    main()