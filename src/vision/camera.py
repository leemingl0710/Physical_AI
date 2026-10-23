"""웹캠 영상 캡처 모듈.

OpenCV의 VideoCapture를 감싼 클래스로, 운영체제에 맞는 카메라 백엔드를 자동으로 고른다.
- macOS  : AVFoundation (맥북 내장 카메라 개발용)
- Windows: DirectShow  (실제 배포 환경, 광각 웹캠)

비전 AI 코어는 이 클래스만 통해 프레임을 받으므로, OS나 카메라가 바뀌어도
상위 코드(얼굴 검출·식별, 자세 분석)는 수정할 필요가 없다.
"""
import sys

import cv2


class Camera:
    """웹캠 하나를 열고 프레임을 읽어오는 클래스.

    `with` 문과 함께 쓰면 블록이 끝날 때 카메라가 자동으로 해제된다.

        with Camera() as cam:
            frame = cam.read()
    """

    def __init__(self, index: int = 0, width: int = 1280, height: int = 720):
        """카메라를 연다.

        Args:
            index: 카메라 번호. 0은 기본 카메라(맥북 내장 캠), 외장 웹캠은 보통 1 이상.
            width, height: 요청할 해상도. 카메라가 지원하지 않으면 가장 가까운 값으로 맞춰진다.
        """
        # OS별 캡처 백엔드 선택.
        # 백엔드를 명시하지 않으면 OpenCV가 임의로 골라 느리거나 실패하는 경우가 있다.
        backend = cv2.CAP_AVFOUNDATION if sys.platform == "darwin" else cv2.CAP_DSHOW
        self.cap = cv2.VideoCapture(index, backend)

        # 카메라를 열지 못한 경우. macOS에서는 대부분 카메라 권한 문제다.
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Camera {index} could not be opened. "
                "On macOS, grant camera access to your terminal/editor in "
                "System Settings > Privacy & Security > Camera."
            )

        # 해상도 설정. 얼굴 인식 정확도와 처리 속도의 균형을 고려해 기본값은 720p.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self):
        """프레임 한 장을 읽는다.

        Returns:
            BGR 형식의 numpy 배열 (높이 x 너비 x 3). 읽기에 실패하면 None.
            ※ OpenCV는 BGR, MediaPipe·face_recognition은 RGB를 쓰므로 넘길 때 변환이 필요하다.
        """
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self):
        """카메라를 해제한다. 해제하지 않으면 다른 프로그램이 카메라를 쓸 수 없다."""
        self.cap.release()

    # --- with 문 지원 (컨텍스트 매니저) ---
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        # 예외가 발생해도 카메라는 반드시 해제된다.
        self.release()
