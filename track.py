from collections import deque
import numpy as np
import argparse
import imutils
import cv2

UPLOAD_FOLDER = 'templates/static/uploads'

def analysis_video(in_file, out_file):
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video", help="path to the (optional) video file")
    args = vars(ap.parse_args())

    greenLower = (29, 86, 6)
    greenUpper = (64, 255, 255)

    cap = cv2.VideoCapture(UPLOAD_FOLDER + '/' + in_file)
    cap.set(3,320)#cv2.CAP_PROP_FRAME_WIDTH
    cap.set(4,240)#cv2.CAP_PROP_FRAME_HEIGHT

    stateSize = 6
    measSize = 4
    contrSize = 0
    ltype = cv2.CV_32F
    end_flag = False
    kf = cv2.KalmanFilter(stateSize, measSize, contrSize, cv2.CV_32F)
    state = np.zeros((stateSize, 1), np.float32)
    meas = np.zeros((measSize, 1), np.float32)    
    cv2.setIdentity(kf.transitionMatrix, 1 )

    kf.measurementMatrix = np.zeros((measSize, stateSize), np.float32)
    kf.measurementMatrix[0,0] = 1.0
    kf.measurementMatrix[3,1] = 1.0
    kf.measurementMatrix[0,4] = 1.0
    kf.measurementMatrix[3,5] = 1.0

    kf.processNoiseCov[0,0] = 1e-2
    kf.processNoiseCov[1,1] = 1e-2
    kf.processNoiseCov[2,2] = 5.0
    kf.processNoiseCov[3,3] = 5.0
    kf.processNoiseCov[4,4] = 1e-2
    kf.processNoiseCov[5,5] = 1e-2

    cv2.setIdentity(kf.measurementNoiseCov, 1e-1)

    ch = 0
    ticks = 0
    found = False
    notFoundCount = 0
    #Main loop
    pos = tmpno = 0
    maskx = 450
    masky = 200
    frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    #vector<cv::Rect> prevBox;
    prevBox = []
    Avgvelocity = 0.0
    TotalVelocity = 0.0
    TotalFrame = 0
    totaldispixel = np.sqrt(707 * 707 + 468 * 468)
    totaldisMM = 18440.4
    BallD = 75.0
    FocusD = 9.5*totaldisMM / BallD
    tmpDis = totaldisMM
    remainframe = 0
    fcc = cv2.VideoWriter_fourcc(*'XVID')
    video = cv2.VideoWriter(UPLOAD_FOLDER + '/' + out_file, fcc, fps, (1920, 1080))

    #Point prev;
    frameno = drawflag = curframe = StartFrameflag = 0
    frameCounter = 1
    speeds = [int]

    while True:
        precTick = ticks
        ticks = cv2.getTickCount()

        dT = (ticks - precTick) / cv2.getTickFrequency(); #seconds       
        #frame1 = np.zeros((1920, 1080,3), np.uint8)
        (grabbed, frame) = cap.read()
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if  grabbed == False:
            break

        frame = imutils.resize(frame, width=1920,height=1080)
        res = frame.copy()
    
        if found :   
            #>>>> Matrix A
            kf.transitionMatrix[2,0] = dT
            kf.transitionMatrix[3,1] = dT
            #<<<< Matrix A
            state = kf.predict() 
            
            width = state[4]
            height = state[5]
            x = int(state[0] - width / 2)
            y = int(state[1] - height / 2)
            predRect = (x,y,width,height)
            center = (state[0],state[1])

            cv2.circle(res, center, 2, (0, 255, 0), -1)
            if frameno > 50 and x + width <= 1000: 
                drawflag = 1
            
        cou = 27        
        balls = []
        ballsBox = []
        tmpcols = 0
        tmprows = 0
        tmpLoc = (0,0)
        maxTemp = 0.0
        #---------image2------------------------
        image2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        ttcou = 0
        for ii in range(pos, cou):    
            tm = ii + 1       
            path = 'patterns/pattern'
            tmpch = str(tm)
            temppattern = cv2.imread(path + tmpch + ".png")
            temppattern = cv2.cvtColor(temppattern, cv2.COLOR_BGR2GRAY)
            
            match_method = cv2.TM_CCORR_NORMED
            res1 = cv2.matchTemplate(image2, temppattern, match_method)           
        
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(res1)
            if match_method == cv2.TM_SQDIFF or match_method == cv2.TM_SQDIFF_NORMED:  
                matchLoc = minLoc
            else: 
                matchLoc = maxLoc

            if maxVal >= 0.97 and maxVal >= maxTemp and matchLoc[0] > maskx and matchLoc[1] > masky and matchLoc[0] < 1000:            
                if ii != 0 and tmpno == 0: 
                    break
                if ii == 0 and tmpno == 0:          
                    tmpno = 1
                    maskx = matchLoc[0] - 100
                    masky = matchLoc[1] - 10
                    curframe = 1
            
                if curframe > 0 and ii - curframe > 0 and ii < curframe - 1: 
                    break

                curframe = ii + 1
                maxTemp = maxVal
                tmpLoc = matchLoc
                ttcou += 1 
                
                tmprows,tmpcols  = temppattern.shape

        if ttcou > 0:
            bBox = [ tmpLoc[0],tmpLoc[1],tmpcols,tmprows ]
            ttcou = 0    
            tmp = []    
            tmp.append([tmpLoc[0],tmpLoc[1]])        
            balls.append(tmp)        
            ballsBox.append(bBox)		
        
        #double deltadis;
        deltaspeed = 0
        if len(ballsBox) != 0:
            deltadis = BallD * FocusD / ballsBox[0][2] #width
            if tmpDis >= deltadis:
                deltaspeed = tmpDis - deltadis
                if TotalFrame == 0 and ballsBox[0][2] < 15: #width
                    StartFrameflag = 1
                    TotalFrame += 1
            
                if TotalFrame == 0 and ballsBox[0][2] >= 15: #width
                    balls.clear()
                    ballsBox.clear()
                
                if StartFrameflag == 1:
                    TotalVelocity = deltaspeed * 3.6*fps / 1000 / TotalFrame
                    Avgvelocity += TotalVelocity
                    prevBox.append(ballsBox[0])
                    TotalFrame += 1
            else:
                balls.clear()
                ballsBox.clear()
        
        if TotalFrame == 0:
            speed = 0
        else:
            speed = Avgvelocity / TotalFrame

        sstr = '( Average Velocity=  ' + str(int(speed)) + ')'

        if TotalVelocity >= 60 and TotalVelocity <= 80:
            speeds.append(int(TotalVelocity))
            
        if frameCounter >= (length-1):
            tSpeed = 0
            for s in range(1,len(speeds)):
                tSpeed = tSpeed + speeds[s]
            eSpeed = tSpeed / (len(speeds) -1)
            print('speed!!!:' + str(int(eSpeed)))
            sstr1 = '( Velocity=  ' + str(int(eSpeed)) + ')'
            cv2.putText(res, sstr1,(10, 100),cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 0, 0), 2)
        
        # Detection result
    
        for i in range(len(balls)):
            cv2.rectangle(res, (ballsBox[i][0], ballsBox[i][1]), (ballsBox[i][0]+ballsBox[i][2],ballsBox[i][1]+ballsBox[i][3]) , (0, 255, 0), 2)

            #cv::Point center;       
            x = int(ballsBox[i][0] + ballsBox[i][2] / 2)
            y = int(ballsBox[i][1] + ballsBox[i][3] / 2)
            cv2.circle(res, (x,y), 2, (20, 150, 20), -1)

            #stringstream sstr;
            sstr = '(' + str(x) + ',' + str(y) + ')'
            cv2.putText(res, sstr, (x + 3, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 150, 20), 2)
        
        if len(balls) == 0:
            notFoundCount += 1
            if notFoundCount >= 100:
                found = False
        else:
            notFoundCount = 0
            meas[0] = ballsBox[0][0] + ballsBox[0][2] / 2
            meas[1] = ballsBox[0][1] + ballsBox[0][3] / 2
            meas[2] = ballsBox[0][2]
            meas[3] = ballsBox[0][3]
            
            if not(found): #First detection!
                # Initialization
                kf.errorCovPre[0,0] = 1
                kf.errorCovPre[1,1] = 1
                kf.errorCovPre[2,2] = 1
                kf.errorCovPre[3,3] = 1
                kf.errorCovPre[4,4] = 1
                kf.errorCovPre[5,5] = 1
                state[0] = meas[0]
                state[1] = meas[1]
                state[2] = 0
                state[3] = 0
                state[4] = meas[2]
                state[5] = meas[3]
                # Initialization
                kf.statePost = state
                found = True
            else:
                kf.correct(meas) #Kalman Correction

        frameCounter = frameCounter + 1
        video.write(res)

    video.release()
    cap.release()
    cv2.destroyAllWindows()