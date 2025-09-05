

from queue import Empty


def dequeue(queue):
    rtn = []
    while True:
        try:
            rtn.append(queue.get(block=False))
        except Empty as e:
            break
    if len(rtn) > 0:
        queue.task_done()
    return rtn

def enqueue(queue, record):
    #queue.put({"tag_name": tag_name, "control": self.matrix[tag_name].realtime_control})
    queue.put(record)