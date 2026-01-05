import sys
import os
import asyncio

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing scripts
# We wrap imports in try-except to avoid crashing if dependencies are missing during development
try:
    from download_video import download_video
    from cut_video import cut_video
    from crop_video.crop_video_deep import batch_process as crop_batch_process
    import auto_subtitle.auto_subtitle as auto_sub
except ImportError as e:
    print(f"Warning: Could not import some scripts: {e}")

from backend.job_manager import JobManager

async def task_download_video(job_manager: JobManager, job_id: str, video_id: str, output_dir: str):
    job_manager.add_job_log(job_id, f"Starting download for {video_id} to {output_dir}")
    
    # Define a callback or patching to capture output could be done here
    # For now, just run the function
    try:
        # download_video is synchronous, run in thread
        def run():
            # Ensure directory exists
            os.makedirs(output_dir, exist_ok=True)
            return download_video(video_id, output_dir)

        video_path = await asyncio.to_thread(run)
        
        if video_path:
            return {"videoFilePath": video_path}
        else:
            raise Exception("Download returned None")
            
    except Exception as e:
        raise e

async def task_cut_video(job_manager: JobManager, job_id: str, video_id: str, video_file_path: str, replayed_parts: list, output_dir: str):
    job_manager.add_job_log(job_id, f"Cutting video {video_file_path} into {len(replayed_parts)} parts...")
    
    def run():
        os.makedirs(output_dir, exist_ok=True)
        # cut_video(video_file, video_id, replayed_parts, output_dir)
        cut_video(video_file_path, video_id, replayed_parts, output_dir, 
                  log_callback=lambda msg: job_manager.add_job_log(job_id, msg))
        
        # Collect results
        parts = []
        for part in replayed_parts:
            part_filename = f"{video_id}_part_{part['position']}.mp4"
            fullpath = os.path.join(output_dir, part_filename)
            if os.path.exists(fullpath):
                parts.append({
                    "path": fullpath,
                    "position": part['position'],
                    "start": part['start'],
                    "end": part['end']
                })
        return {"parts": parts}

    return await asyncio.to_thread(run)

async def task_crop_video(job_manager: JobManager, job_id: str, input_dir: str, output_dir: str):
    job_manager.add_job_log(job_id, f"Cropping videos from {input_dir} to {output_dir}")
    
    def run():
        os.makedirs(output_dir, exist_ok=True)
        crop_batch_process(input_dir, output_dir)
        
        # Collect outputs
        outputs = []
        for f in os.listdir(output_dir):
            if f.endswith(".mp4"):
                outputs.append({
                    "path": os.path.join(output_dir, f),
                    "sourcePath": "unknown" # mapping would require more complex tracking
                })
        return {"outputs": outputs}

    return await asyncio.to_thread(run)

async def task_subtitle_video(job_manager: JobManager, job_id: str, input_dir: str, output_dir: str, model_size: str):
    job_manager.add_job_log(job_id, f"Adding subtitles from {input_dir} to {output_dir} using model {model_size}")
    
    def run():
        os.makedirs(output_dir, exist_ok=True)
        # auto_subtitle.auto_subtitle.batch_process(input_dir, output_dir)
        # NOTE: existing script doesn't take model_size in batch_process, only in add_subtitles
        # We might want to modify the existing script or just accept default 'medium'
        # The existing batch_process hardcodes 'medium'.
        # For now we use the existing batch_process
        auto_sub.batch_process(input_dir, output_dir)
        
        outputs = []
        for f in os.listdir(output_dir):
            if f.endswith(".mp4") and "_subtitled" in f:
                 outputs.append({
                    "path": os.path.join(output_dir, f),
                    "sourcePath": "unknown"
                })
        return {"outputs": outputs}

    return await asyncio.to_thread(run)
