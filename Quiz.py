import cv2
import csv
import time
import cvzone
from cvzone.HandTrackingModule import HandDetector

detector = HandDetector(detectionCon=0.8, maxHands=2)
video = cv2.VideoCapture(0)

prev_time = 0

class ARD():
    def __init__(self, data):
        self.Pertanyaan = data[0]
        self.Pilihan1 = data[1]
        self.Pilihan2 = data[2]
        self.Pilihan3 = data[3]
        self.Pilihan4 = data[4]
        self.Jawaban = int(data[5])

        self.JawabanSiswa = None

    def update(self, fingers):
        if fingers == [0, 1, 0, 0, 0]:  # Jika 1 jari diangkat
            self.JawabanSiswa = 1
        elif fingers == [0, 1, 1, 0, 0]:  # Jika 2 jari diangkat
            self.JawabanSiswa = 2
        elif fingers == [0, 1, 1, 1, 0]:  # Jika 3 jari diangkat
            self.JawabanSiswa = 3
        elif fingers == [0, 1, 1, 1, 1]:  # Jika 4 jari diangkat
            self.JawabanSiswa = 4
        elif fingers == [1, 1, 1, 1, 1]:  # Jika 5 jari diangkat
            self.JawabanSiswa = None

    def drawQuestion(self, img, fontSize=2, maxLineWidth=600, offset=10, border=1, color=(0, 0, 0)):
        lines = []
        words = self.Pertanyaan.split()
        temp_line = ''
        for word in words:
            if cv2.getTextSize(temp_line + ' ' + word, cv2.FONT_HERSHEY_SIMPLEX, fontSize, border)[0][
                0] <= maxLineWidth:
                temp_line += ' ' + word
            else:
                lines.append(temp_line.strip())
                temp_line = word
        lines.append(temp_line.strip())

        y = 100
        for line in lines[:2]:  # Hanya tampilkan dua baris pertama
            img, _ = cvzone.putTextRect(img, line, [100, y], fontSize, 2, offset=10, border=1,
                                        colorT=(255, 255, 0), colorB=(255, 255, 0), colorR=(0, 0, 0))
            y += 50
        return img

# Import CSV File
pathCSV = "Pertanyaan.csv"
with open(pathCSV, newline='\n') as f:
    reader = csv.reader(f)
    data = list(reader)[1:]

# Membuat Objek untuk Pertanyaan
ardlist = []
for q in data:
    ardlist.append(ARD(q))

print(len(data))

qNo = 0
qTotal = len(data)

# Kotak reset
reset_box = [0, 0, 80, 50]  # [x1, y1, width, height]

def on_mouse_click(event, x, y, flags, param):
    global qNo, score
    if event == cv2.EVENT_LBUTTONDOWN:
        if reset_box[0] < x < reset_box[0] + reset_box[2] and reset_box[1] < y < reset_box[1] + reset_box[3]:
            qNo = 0
            score = 0

cv2.namedWindow("img")
cv2.setMouseCallback("img", on_mouse_click)

running = True

class Quiz:

    while running:
        ret, frame = video.read()
        frame = cv2.flip(frame, 1)
        hands, img = detector.findHands(frame)

        if qNo < qTotal:
            ard = ardlist[qNo]

            # Gambar pertanyaan dengan dua baris
            img = ard.drawQuestion(img, 2, 1000, 10, 1, color=(255, 255, 0))

            img, bbox1 = cvzone.putTextRect(img, ard.Pilihan1, [100, 250], 2, 2, offset=10, border=1,
                                            colorR=(0, 0, 0), colorT=(255, 255, 0), colorB=(255, 255, 0))
            img, bbox2 = cvzone.putTextRect(img, ard.Pilihan2, [400, 250], 2, 2, offset=10, border=1,
                                            colorR=(0, 0, 0), colorT=(255, 255, 0), colorB=(255, 255, 0))
            img, bbox3 = cvzone.putTextRect(img, ard.Pilihan3, [100, 350], 2, 2, offset=10, border=1,
                                            colorR=(0, 0, 0), colorT=(255, 255, 0), colorB=(255, 255, 0))
            img, bbox4 = cvzone.putTextRect(img, ard.Pilihan4, [400, 350], 2, 2, offset=10, border=1,
                                            colorR=(0, 0, 0), colorT=(255, 255, 0), colorB=(255, 255, 0))

            if hands and len(hands) > 0:  # Pastikan ada setidaknya satu tangan terdeteksi
                lmList = hands[0]['lmList']
                fingers = detector.fingersUp(hands[0])  # Ubah menjadi hands[0]
                ard.update(fingers)
                if ard.JawabanSiswa is not None:
                    time.sleep(3)
                    qNo += 1

        else:
            score = sum(1 for ard in ardlist if ard.Jawaban == ard.JawabanSiswa)  # Menghitung skor
            score = round((score / qTotal) * 100, 2)
            img, _ = cvzone.putTextRect(img, "Quiz Selesai!", [70, 200], 5, 3, offset=10, border=5,
                                        colorR=(0, 0, 0), colorT=(255, 255, 0), colorB=(255, 255, 0))
            img, _ = cvzone.putTextRect(img, f'Nilai: {score}%', [70, 300], 5, 3, offset=10, border=5,
                                        colorR=(0, 0, 0), colorT=(255, 255, 0), colorB=(255, 255, 0))

        if qNo == qTotal:
            # Tampilkan kotak reset
            cv2.rectangle(img, (reset_box[0], reset_box[1]), (reset_box[0] + reset_box[2], reset_box[1] + reset_box[3]),
                        (0, 0, 0), cv2.FILLED)
            img, _ = cvzone.putTextRect(img, "Reset", [reset_box[0] + 15, reset_box[1] + 30], 1, 2, offset=5,
                                        colorR=(0, 0, 255), colorT=(0, 255, 255), colorB=(0, 0, 255))

        barValue = 100 + (400 // qTotal) * qNo
        cv2.rectangle(img, (100, 400), (barValue, 450), (255, 255, 0), cv2.FILLED)
        cv2.rectangle(img, (100, 400), (500, 450), (0, 0, 0), 5)
        img, _ = cvzone.putTextRect(img, f'{round((qNo / qTotal) * 100)}%', [530, 430], 1, 1, offset=10,
                                    colorR=(0, 0, 0), colorT=(255, 255, 0), colorB=(255, 255, 0))

        cv2.imshow("img", img)

        if cv2.waitKey(1) == ord('q'):
            running = False
            break
        
    cv2.destroyAllWindows()
