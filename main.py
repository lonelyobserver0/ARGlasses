import multiprocessing
import cursor_handler
import display_handler

if __name__ == '__main__':
    queue = multiprocessing.Queue()

    p1 = multiprocessing.Process(target=cursor_handler.main, args=(queue,))
    p2 = multiprocessing.Process(target=display_handler.main, args=(queue,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
    