import cv2

haar_cascade = cv2.CascadeClassifier('cascade4.xml')
cap = cv2.VideoCapture(0)
while cap.isOpened():
    _, frame = cap.read()
    gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hands = haar_cascade.detectMultiScale(gray_img, scaleFactor=1.33, minNeighbors=7)
#Plot hand
    for (x, y, w, h) in hands:
        print(f"hands:{hands}\n")
        print(f"x:{x}, y:{y}, w:{w}, h:{h}")
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
    cv2.imshow('', frame)
    if (cv2.waitKey(1) & 0xFF == ord('q')):
        break

cv2.destroyAllWindows()
