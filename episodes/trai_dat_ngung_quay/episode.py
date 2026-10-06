"""Tập mẫu: Nếu Trái Đất ngừng quay 1 giây?"""
from hh2d import Actor, Cam, Scene

TITLE = "Nếu Trái Đất ngừng quay 1 giây?"
VOICE = dict(voice="thanh_phong", speed=1.4)       # KorvaTTS
# MUSIC = "nhac_nen.mp3"                            # bỏ file nhạc vào thư mục tập rồi mở dòng này

SCENES = [
    # 1. Hook
    Scene(
        say="Nếu *Trái Đất* đột nhiên ngừng quay, chỉ trong một giây thôi...",
        fx=["twinkle"],
        cam=Cam(zoom=(1.0, 1.08), focus=(1100, 540)),
        actors=[
            Actor("hanh_tinh", 250, 170, enter="pop", enter_at=.2, idle="float"),
            Actor("trai_dat", 1350, 520, enter="pop", enter_at=.45, idle="float",
                  kw=dict(r=280, spin=.9, face="happy")),
            Actor("mui_ten_cong", 1350, 200, enter="grow", enter_at=1.1, scale=.85, idle="bob"),
            Actor("giao_su", 480, 600, enter="slide_left", talk=True, idle="breathe",
                  kw=dict(pose="wave")),
        ],
    ),
    # 2. Câu hỏi
    Scene(
        say="Chuyện gì sẽ xảy ra với chúng ta?",
        transition="zoom",
        fx=["twinkle", ("rays", dict(x=760, y=420, color=(24, 36, 74)))],
        cam=Cam(zoom=(1.05, 1.12), punch=[.3], focus=(800, 500)),
        actors=[
            Actor("giao_su", 760, 600, enter=None, talk=True, idle="breathe", kw=dict(pose="think")),
            Actor("dau_hoi", 1150, 260, enter="pop", enter_at=.2, idle="wiggle", scale=.9),
            Actor("dau_hoi", 1420, 520, enter="pop", enter_at=.45, idle="hop", scale=.7),
            Actor("dau_hoi", 380, 230, enter="pop", enter_at=.7, idle="sway", scale=.6, flip=True),
        ],
    ),
    # 3. Tốc độ quay
    Scene(
        say="Hiện tại, Trái Đất đang tự quay với tốc độ khoảng *1.670 km/h* ở xích đạo.",
        read="Hiện tại, Trái Đất đang tự quay với tốc độ khoảng một nghìn sáu trăm bảy mươi ki lô mét một giờ ở xích đạo.",
        fx=["twinkle", ("rays", dict(x=900, y=560, color=(22, 33, 70), speed=.15))],
        cam=Cam(zoom=(1.0, 1.1), focus=(900, 520), punch=[2.6]),
        actors=[
            Actor("trai_dat", 900, 580, enter="spin_in", enter_dur=.7, kw=dict(r=320, spin=1.6)),
            Actor("mui_ten_cong", 900, 230, enter="grow", enter_at=.6, idle="bob"),
            Actor("chu", 900, 120, enter="pop", enter_at=2.6, idle="pulse",
                  kw=dict(text="1.670 km/h", size=120, color=(255, 110, 80))),
            Actor("giao_su", 1620, 640, scale=.75, flip=True, enter="slide_right", enter_at=.3,
                  talk=True, idle="breathe", kw=dict(pose="point")),
        ],
    ),
    # 4. Mọi thứ quay cùng
    Scene(
        say="Nhưng ta không hề thấy chóng mặt, vì mọi thứ đều quay cùng với nó.",
        bg="troi",
        cam=Cam(zoom=(1.0, 1.05), pan=((-40, 0), (40, 0))),
        actors=[
            Actor("mat_troi", 230, 180, enter="drop", idle="float"),
            Actor("may", 1500, 170, enter="slide_right", enter_at=.2, idle="float", move=(-25, 0)),
            Actor("may", 800, 120, scale=.7, enter="slide_right", enter_at=.4, idle="float", move=(-35, 0)),
            Actor("nha", 420, 760, enter="drop", enter_at=.3, scale=1.3, idle="jelly"),
            Actor("cay", 650, 745, enter="drop", enter_at=.45, scale=1.2, idle="sway"),
            Actor("nguoi_nho", 860, 790, enter="pop", enter_at=.6, idle="hop"),
            Actor("nguoi_nho", 980, 790, enter="pop", enter_at=.75, idle="hop", kw=dict(color=(90, 160, 240))),
            Actor("o_to", 0, 840, enter=None, path=[(0, -150, 840), (4.5, 1150, 840)], idle="shake"),
            Actor("giao_su", 1500, 620, enter="slide_right", talk=True, idle="breathe", kw=dict(pose="shrug")),
        ],
    ),
    # 5. Phanh gấp
    Scene(
        say="Nhưng nếu nó *dừng đột ngột*...",
        dur=3.2,
        fx=["twinkle", ("flash", dict(t=1.0))],
        cam=Cam(zoom=(1.0, 1.0), punch=[1.0], shake=[(1.0, .9, 38)]),
        actors=[
            Actor("trai_dat", 960, 560, enter=None, kw=dict(r=330, spin=1.8, stop_at=1.0, face="scared")),
            Actor("bien_stop", 1500, 260, enter="drop", enter_at=.75, idle="wiggle", scale=1.2),
            Actor("giao_su", 330, 640, scale=.7, enter="pop", enter_at=1.2, talk=True,
                  kw=dict(pose="shock", face="shock")),
        ],
    ),
    # 6. Hất văng
    Scene(
        say="thì mọi thứ trên mặt đất sẽ bị *hất văng* về phía đông!",
        transition="cut",
        fx=["speed"],
        cam=Cam(zoom=(1.0, 1.06), shake=[(0, 2.5, 10)]),
        actors=[
            Actor("trai_dat", 250, 1330, enter=None, kw=dict(r=720, spin=0)),
            Actor("chu", 1560, 110, enter="pop", enter_at=.5, idle="pulse",
                  kw=dict(text="PHÍA ĐÔNG", size=86, color=(255, 214, 80))),
            Actor("mui_ten", 1560, 210, enter="slide_left", enter_at=.7, idle="bob"),
            Actor("nha", -150, 640, enter="fade", enter_dur=.01, enter_at=.0, sound="whoosh",
                  move=(1150, -260), gravity=120, spin=140),
            Actor("cay", -150, 760, enter="fade", enter_dur=.01, enter_at=.3, sound="whoosh",
                  move=(1300, -330), gravity=150, spin=-200),
            Actor("con_bo", -150, 560, enter="fade", enter_dur=.01, enter_at=.7, sound="whoosh",
                  move=(1100, -150), gravity=90, spin=260),
            Actor("o_to", -150, 820, enter="fade", enter_dur=.01, enter_at=1.0, sound="whoosh",
                  move=(1350, -380), gravity=160, spin=-300),
            Actor("nguoi_nho", -150, 700, enter="fade", enter_dur=.01, enter_at=1.3, sound="whoosh",
                  move=(1250, -300), gravity=120, spin=400),
            Actor("giao_su", -250, 600, scale=.75, enter="fade", enter_dur=.01, enter_at=1.7, sound="whoosh",
                  move=(1000, -220), gravity=100, spin=220, talk=True, kw=dict(pose="fly", face="shock")),
        ],
    ),
    # 7. So với máy bay
    Scene(
        say="Nhanh gần gấp đôi *máy bay phản lực*!",
        dur=3.6,
        fx=["speed", "twinkle"],
        cam=Cam(zoom=(1.0, 1.08), punch=[1.6]),
        actors=[
            Actor("may_bay", 0, 300, scale=1.5, enter=None, path=[(0, -400, 300), (4.0, 1500, 300)], idle="bob"),
            Actor("nha", -200, 680, enter="fade", enter_dur=.01, enter_at=.4, sound="whoosh",
                  move=(1500, 0), spin=60, idle="wiggle", scale=1.2),
            Actor("chu", 1500, 600, enter="pop", enter_at=1.6, idle="pulse", sound="ding",
                  kw=dict(text="x2", size=180, color=(255, 110, 80))),
        ],
    ),
    # 8. Kết
    Scene(
        say="May mắn là chuyện này gần như *không thể* xảy ra. Đăng ký kênh để xem thêm nhé!",
        fx=["twinkle", ("rays", dict(x=960, y=560, color=(24, 36, 74), speed=.3)), ("confetti", dict(seed=5))],
        cam=Cam(zoom=(1.08, 1.0)),
        dur=6.0,
        actors=[
            Actor("trai_dat", 330, 470, enter="pop", idle="float", kw=dict(r=200, spin=.6, face="happy")),
            Actor("giao_su", 960, 600, enter="rise", talk=True, idle="hop", kw=dict(pose="cheer")),
            Actor("nut_dang_ky", 1520, 420, enter="pop", enter_at=3.0, idle="pulse"),
            Actor("sao", 1700, 300, enter="pop", enter_at=3.3, idle="wiggle"),
            Actor("sao", 1350, 300, enter="pop", enter_at=3.5, idle="wiggle", kw=dict(r=16)),
        ],
    ),
]
