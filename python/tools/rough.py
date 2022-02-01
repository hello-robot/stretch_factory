def check_FPS(data):
    global check_log
    MIN_FPS = 29.3
    streams = ['Depth','Color','Gyro','Accel']
    for s in streams:
        fps = get_fps(data,s,'0')
        if fps>MIN_FPS:
            print(Fore.GREEN+'[Pass] %s Rate : %f FPS'%(s,fps))
            check_log.append('[Pass] %s Rate : %f FPS'%(s,fps))
        else:
            print(Fore.RED+'[Fail] %s Rate : %f FPS below %d FPS'%(s,fps,MIN_FPS))
            check_log.append('[Fail] %s Rate : %f FPS below %d FPS'%(s,fps,MIN_FPS))

def get_fps(data,stream,t):
    timestamps = []
    for ll in data:
        tag = stream+','+t
        if tag in ll:
            print(ll.split(',')[-1][-2])
            try:
                l = ll.split(',')[-1][-2]
                timestamp = float(l)
                lines.append(timestamp)
            except:
                None

    duration = (timestamps[-1]-timestamps[0])/1000
    avg_fps = len(timestamps)/duration
    return avg_fps