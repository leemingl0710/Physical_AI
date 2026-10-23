"""웹캠 연결 확인용 테스트 스크립트.

사용법 (프로젝트 루트에서 실행):
    python scripts/camera_test.py              # 실시간 미리보기 창 (q 또는 ESC로 종료)
    python scripts/camera_test.py --snapshot   # 한 장만 찍어 data/snapshot.jpg로 저장
    python scripts/camera_test.py --index 1    # 다른 카메라(외장 웹캠 등) 사용
"""
import argparse
import os
import sys
import time

import cv2

# scripts/ 폴더에서 실행해도 src 패키지를 찾을 수 있도록 프로젝트 루트를 import 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.vision.camera import Camera  # noqa: E402  (경로 추가 후 import 해야 하므로 위치 예외)


def main():
    # 명령줄 옵션 정의
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=0)        # 카메라 번호
    parser.add_argument("--snapshot", action="store_true")     # 사진 한 장만 저장하고 종료
    args = parser.parse_args()

    with Camera(args.index) as cam:
        # 맥북 카메라는 켜진 직후 몇 프레임이 검게 나오므로(노출 조정 중) 10장을 버린다.
        for _ in range(10):
            frame = cam.read()
        if frame is None:
            sys.exit("Camera opened but returned no frame.")

        # frame.shape = (높이, 너비, 채널 수)
        h, w = frame.shape[:2]
        print(f"Camera {args.index} OK: {w}x{h}")

        # --snapshot 모드: 한 장 저장 후 종료 (창을 띄울 수 없는 환경에서 연결 확인용)
        if args.snapshot:
            os.makedirs("data", exist_ok=True)
            cv2.imwrite("data/snapshot.jpg", frame)
            print("Saved data/snapshot.jpg")
            return

        # 미리보기 모드: 프레임을 계속 읽어 창에 표시
        prev = time.time()
        while True:
            frame = cam.read()
            if frame is None:  # 카메라 연결이 끊긴 경우
                break

            # FPS(초당 프레임 수) 계산: 직전 프레임과의 시간 차이의 역수
            now = time.time()
            fps = 1.0 / max(now - prev, 1e-6)  # 0으로 나누기 방지
            prev = now

            # 화면 좌측 상단에 FPS를 초록색 글씨로 표시
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Camera Test", frame)

            # 1ms 동안 키 입력 대기. q 또는 ESC(27)를 누르면 종료.
            # (waitKey를 호출해야 창이 실제로 갱신된다)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
