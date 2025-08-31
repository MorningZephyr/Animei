"""
Queue manager for handling image generation requests.
"""

import asyncio
from typing import Optional
from schema import GenerationRequest


class QueueManager:
    """Manages the queue of image generation requests and processes them sequentially."""
    
    def __init__(self, image_generator):
        self.image_generator = image_generator  # Referencing the image generator class
        
        # Queue system for handling multiple requests
        self.generation_queue = asyncio.Queue(maxsize=50)  # Limit queue size
        self.current_request: Optional[GenerationRequest] = None
        self.is_processing: bool = False
        self.worker_task: Optional[asyncio.Task] = None
    
    async def start_worker(self):
        """Start the queue worker to process requests sequentially"""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._process_generation_requests())
            print("🔄 Queue worker started")
    
    async def stop_worker(self):
        """Stop the queue worker"""
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            print("⏹️ Queue worker stopped")
    
    async def _process_generation_requests(self):
        """Background worker that processes requests from the queue"""
        print("🔄 Queue worker running...")
        while True:
            try:
                # Wait for a request (entire function falls asleep if queue is empty)
                # Control is yielded to event loop until request is enqueued
                request = await self.generation_queue.get() # Checks the queue size and blocks if it's empty
                
                self.current_request = request
                self.is_processing = True
                print(f"🎨 Processing request {request.request_id[:8]}... (Queue: {self.generation_queue.qsize()})")
                
                # Generate the image using the image generator
                image = await self.image_generator.generate_image(
                    prompt=request.prompt,
                    negative_prompt=request.negative_prompt,
                    num_inference_steps=request.num_inference_steps,
                    cfg_scale=request.cfg_scale,
                    width=request.width,
                    height=request.height
                )
                
                # Mark task as done
                self.generation_queue.task_done()
                self.current_request = None
                self.is_processing = False
                
                print(f"✅ Completed request {request.request_id[:8]}")
                
                # Call the callback function to deliver the image
                if request.callback:
                    try:
                        await request.callback(image, request)
                    except Exception as callback_error:
                        print(f"❌ Callback error for request {request.request_id[:8]}: {callback_error}")
                else:
                    print(f"⚠️  No callback set for request {request.request_id[:8]} - image not delivered")
                
            except asyncio.CancelledError:
                print("🛑 Queue worker cancelled")
                break
            except Exception as e:
                print(f"❌ Error processing request: {e}")
                self.generation_queue.task_done()
                self.current_request = None
                self.is_processing = False
    
    async def add_to_queue(self, request: GenerationRequest) -> bool:
        """Add a request to the queue. Returns True if added, False if queue is full"""
        try:
            await self.generation_queue.put(request)
            print(f"📥 Added request to queue. Position: {self.generation_queue.qsize()}")
            return True
        except asyncio.QueueFull:
            print("❌ Queue is full! Cannot add more requests.")
            return False
    
    def get_queue_status(self) -> dict:
        """Get current queue status"""
        return {
            "queue_size": self.generation_queue.qsize(),
            "is_processing": self.is_processing,
            "current_request_id": self.current_request.request_id[:8] if self.current_request else None,
            "max_size": self.generation_queue.maxsize
        }
    
    @property
    def is_running(self) -> bool:
        """Check if the queue worker is running."""
        return self.worker_task is not None and not self.worker_task.done()
