import cv2
import matplotlib.pyplot as plt
import numpy as np


cap = cv2.VideoCapture(0)

def get_snapshot():
    ok, raw = cap.read()
    if not ok or raw is None:
        print("amera read failed")
        return None

    raw = cv2.resize(raw,(640,480))
    return raw

while True:
    raw = get_snapshot()
    if raw is None:
        break
    

    # cv2.imshow("webcame", raw)
    hsv = cv2.cvtColor(raw, cv2.COLOR_RGB2HSV)





    # plt.imshow(hsv)
    # plt.title("HSV image")
    # plt.axis("off")
    # plt.show()


    lower = np.array([0, 50, 50]) 
    upper = np.array([179, 255, 255])

    mask = cv2.inRange(hsv, lower, upper) #everything between lower nad upper values. outputs a binary w/ 2 colors

    # plt.figure(figsize=(14,8))
    # cv2.imshow("hsv color mask", mask)
    # plt.imshow(mask, cmap="gray")
    # plt.title("hev color mask")
    # plt.axis("off")
    # plt.show()


    open_kernel = np.ones((3, 3), np.uint8) #blurs everything and removes the smoller dots ig. open = erosion followed by dialtion
    #the normal big stuff get shrunken but hten dilated but noise is removed completely so gone

    opened_mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        open_kernel,
        iterations=1
    )

    # plt.figure(figsize=(14,8))
    # plt.imshow(opened_mask, cmap="gray")
    # plt.title("kernel removes small dots")
   
    # plt.axis("off")
    # plt.show()
    
    contours, _ = cv2.findContours(
        opened_mask, #image to find contours on
        cv2.RETR_EXTERNAL,  #retreiv external: whati nfo u wanna retrieve which is external boundaries
        cv2.CHAIN_APPROX_SIMPLE #contour alg
    )

    all_contours_img = raw.copy()
    cv2.drawContours(
        all_contours_img, #image to draw them on
        contours, #which contours to draw
        -1,  #which index (-1 = all)
        (255, 55, 255),  #color to draw them in
        2 #width of contour lines
    )

    # plt.figure(figsize=(14,8))
    # plt.imshow(all_contours_img)
   
    # plt.title("kall contours")
    # plt.axis("off")
    # plt.show()





    squares_count = 0
    squares_img = raw.copy()

    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area < 100:
            continue
        perimeter = cv2.arcLength(cnt, True)

        if perimeter == 0: #if its an open line not a closed perimeter
            continue

        #approx to a polyhgon
        approx = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)

        #square - 4 corners
        if len(approx) != 4:
            continue

        if not cv2.isContourConvex(approx):
            continue
        
        #rotated rectangle 
        rect = cv2.minAreaRect(cnt)
        (cx, cy), (w, h), angle = rect

        if w == 0 or h == 0:
            continue

        aspect_ratio = max(w, h) / min(w, h)  

        if aspect_ratio > 1.5:
            continue

        box_area = w * h
        extent = area / box_area
        if extent < 0.45: #if shape fills enough of the bounding box
            continue
        squares_count += 1

        box = cv2.boxPoints(rect)
        box = np.int32(box)

        cv2.drawContours(squares_img, [box], 0, (255, 255, 255), 3)

    # plt.figure(figsize=(14,8))
    # plt.imshow(squares_img)
    # plt.title(f"square conunt: {squares_count}")
    # plt.axis("off")
    # plt.show()
    cv2.imshow(f"square count: {squares_count} ", squares_img)

    if cv2.waitKey(1) == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()