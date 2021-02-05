import cv2
import numpy as np
angle_factor = 0.8
sw = 0.3
sh = 1
frame_num = 0
solid_back_color = (50, 50, 50)
backgroud = cv2.imread('./img.png')
wght = "./YoloFiles/yolov3.weights"
cnfg = "./YoloFiles/yolov3.cfg"
LblPath = "./YoloFiles/coco.names"
background = cv2.imread('./icons/AITFSC.png')

Lbls = open(LblPath).read().strip().split("\n")
net = cv2.dnn.readNetFromDarknet(cnfg, wght)
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
boxes = []
def box_values(i):
    (x, y) = (boxes[i][0], boxes[i][1])
    (w, h) = (boxes[i][2], boxes[i][3])
    cen = [int(x + w / 2), int(y + h / 2)]
    return x,w,y,h,cen
#bird eye is not used right now
def Bird_eye_transform(H,W,cen):
    #src = np.float32([[952,669],[1222,559],[95,286],[404,286]])
    src = np.float32([[1075,669],[1278,496],[4,286],[294,226]])
    dst = np.float32([[0, H], [W, H], [0, 0], [W, 0]])
    M = cv2.getPerspectiveTransform(src, dst)
    pts = np.array([[cen]], dtype="float32")
    warped_pt = cv2.perspectiveTransform(pts, M)[0][0]
    warped_pt_scaled = [int(warped_pt[0] * 0.3), int(warped_pt[1] * 1)]
    return warped_pt_scaled



def euclid_dist(A,B):
    A__B = ( (A[0] - B[0])**2  +  (A[1] - B[1])**2 )**0.5
    return A__B



def closeness(OBJ1,OBJ2):

    A_B = euclid_dist(OBJ1[2],OBJ2[2]) 
    
    if (OBJ1[1] < OBJ2[1]): #compare the length of both ojcet detected
        assum_W = OBJ1[0] # width is assumed to be shortest on compare
        assum_H = OBJ1[1] # height is assumed to be shortest on compare  
    else:
        assum_W = OBJ2[0] # width is assumed to be shortest on compare
        assum_H = OBJ2[1] # height is assumed to be shortest on

    
    
    
    def Tan_Sin(Tan):
        
        Sin = abs(Tan/((1+Tan**2)**0.5))

        return Sin

    def Tan_Cos(Tan):
        Cos = abs(1/((1+Tan**2)**0.5))

        return Cos
    
    
    Tan = 0
    
    try:
        Tan=( OBJ2[2][1] - OBJ1[2][1] ) / ( OBJ2[2][0] - OBJ1[2][0] )
    
    except ZeroDivisionError:
        T = 1.633123935319537e+16
    
    Sin = Tan_Sin(Tan)
    Cos = Tan_Cos(Tan)
    
    d_hor = Cos*A_B
    d_ver = Sin*A_B

    vc_calib_hor = assum_W
    vc_calib_ver = assum_H
    #c_calib_hor = assum_W
    #c_calib_ver = assum_H


    
    
    if (0<d_hor<vc_calib_hor and 0<d_ver<vc_calib_ver):
        return 1 #at risk red
    
    #elif 0<d_hor<c_calib_hor and 0<d_ver<c_calib_ver:
        #return 2 # yellow maintain distance
    else:
        return 0 #safe



def yolo(frame):
    
    
    (H, W) = frame.shape[:2]
    #frm = np.zeros((int(H*sh),int(W*sw),3),np.uint8)
    #frm[:] = solid_back_color
    frm = background.copy()
    #bckgrnd[]
    #img3[100:400,100:400,:] = img2[100:400,100:400,:]
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),swapRB=True, crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)
    confidences = []
    classIDs = []
    global boxes
    boxes.clear()
    
    for outputs in layerOutputs:
        
        for detection in  outputs:
    
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
    
            if Lbls[classID] == "truck"or"car"or"bus"or"motorbike":
                
                if confidence > 0.5 :
                    
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    classIDs.append(classID)
    
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5,0.5)
    

    if len(idxs) > 0:
    
        idf = idxs.flatten()
        centroid = []
        obj_info = []
        status = []
        close_pair = []
        s_close_pair = []
        
        for i in idf:
            _,w,_,h,cen = box_values(i)
            centroid.append(cen)
            obj_info.append([w, h, cen])
            status.append(0)
        
        for i in range(len(centroid)):
            
            for j in range(len(centroid)):
                
                Value = closeness(obj_info[i],obj_info[j])
                if Value == 1:
                    close_pair.append([centroid[i], centroid[j]])
                    status[i] = 1
                    status[j] = 1
                elif Value == 2:
                    s_close_pair.append([centroid[i], centroid[j]])
                    if status[i] != 1:
                        status[i] = 2
                    if status[j] != 1:
                        status[j] = 2
    
        total_p = len(centroid)
        low_risk_p = status.count(2)
        high_risk_p = status.count(1)
        safe_p = status.count(0)
        kk = 0
    
        for i in idf:

            x,w,y,h,cen = box_values(i)
            warped_pt_scaled = Bird_eye_transform(H,W,cen)

            if status[kk] == 1:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (66, 66, 255), 2)
                cv2.circle(frm,(warped_pt_scaled[0]*2, warped_pt_scaled[1]),
                                    10,(66, 66, 255),-1)

            elif status[kk] == 0:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (128, 255, 0), 2)
                cv2.circle(frm,(warped_pt_scaled[0]*2, warped_pt_scaled[1]),
                                    10,(128, 255, 0),-1)

            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 120, 255), 2)
                #cv2.circle(frm,(warped_pt_scaled[0], warped_pt_scaled[1]),10,(0, 120, 255),-1)

            kk += 1
    
        for h in close_pair:
            
            cv2.line(frame, tuple(h[0]), tuple(h[1]), (66, 66, 255), 2)
            centr_pnt1 = Bird_eye_transform(H,W*2,h[0])
            centr_pnt2 = Bird_eye_transform(H,W*2,h[1])
            cv2.line(frm, tuple(centr_pnt1), tuple(centr_pnt2), (66, 66, 255), 5)
                
        for b in s_close_pair:
            cv2.line(frame, tuple(b[0]), tuple(b[1]), (128, 255, 0), 2)
            #centr_pnt1 = Bird_eye_transform(H,W,b[0])
            #centr_pnt2 = Bird_eye_transform(H,W,b[1])
            #cv2.line(frm, tuple(centr_pnt1), tuple(centr_pnt2), (0, 255, 255), 5)
                

    return  frame,total_p, high_risk_p, safe_p
            
