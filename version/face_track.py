import time
import mediapipe as mp
import cv2

def realtime_track(videosource):
    cap = cv2.VideoCapture(videosource)
    if not cap.isOpened():
        print("Error: Camera is not accessible.")
        return None
    pTime = 0
    mpFace = mp.solutions.face_detection
    face_detection_model = mpFace.FaceDetection(
        min_detection_confidence=0.7,  # 提高最小置信度
        model_selection=0)  # 使用短距离模型
    myDraws = mp.solutions.drawing_utils

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to read from the camera.")
            break

        process_frame(frame, face_detection_model)

        # FPS 计算
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(frame, f"FPS: {int(fps)}", (30, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        cv2.imshow("Frame", frame)

        if cv2.waitKey(18) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def process_frame(frame, face_detection_model):
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detection_model.process(img_rgb)
    
    if results.detections:
        for detection in results.detections:
            boxLms = detection.location_data.relative_bounding_box
            
            # 计算绝对坐标
            h, w, _ = frame.shape
            x_min = int(boxLms.xmin * w)
            y_min = int(boxLms.ymin * h)
            box_width = int(boxLms.width * w)
            box_height = int(boxLms.height * h)

            # 绘制边界框
            cv2.rectangle(frame, (x_min, y_min), (x_min + box_width, y_min + box_height), (0, 255, 0), 2)
            cv2.putText(frame, f'score: {int(detection.score[0] * 100)}%', 
                        (x_min, y_min - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)


if __name__ == "__main__":
    realtime_track(r"C:\Users\song2\Desktop\AIrobot\DeskBot\version\fece_test.mp4")
