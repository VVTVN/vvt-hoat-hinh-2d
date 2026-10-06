"""Video dài: gom các tập Short thành một video 9-11 phút.

Thêm tập vào danh sách TAP theo thứ tự muốn phát. Mỗi tập ~40-50s -> cần 12-14 tập.
"""
from hh2d import Actor, Cam, Scene
from hh2d.compile import gom

TITLE = "Những câu hỏi khoa học thú vị nhất"
VOICE = dict(voice="thanh_phong", speed=1.4)

TAP = [
    "trai_dat_ngung_quay",
    "bau_troi_mau_xanh",
]

MO_DAU = [
    Scene(
        say="Xin chào! Hôm nay chúng ta sẽ cùng giải đáp những *câu hỏi khoa học* thú vị nhất về thế giới quanh ta.",
        fx=["twinkle", ("rays", dict(x=960, y=560, color=(24, 36, 74), speed=.25))],
        cam=Cam(zoom=(1.0, 1.08)),
        actors=[
            Actor("hanh_tinh", 260, 200, enter="pop", enter_at=.3, idle="float"),
            Actor("trai_dat", 1450, 520, enter="spin_in", enter_at=.6, idle="float",
                  kw=dict(r=240, spin=.8, face="happy")),
            Actor("mat_troi", 1700, 170, scale=.7, enter="pop", enter_at=1.0, idle="float"),
            Actor("giao_su", 600, 600, enter="slide_left", talk=True, idle="breathe", kw=dict(pose="wave")),
        ],
    ),
    Scene(
        say="Bắt đầu thôi!",
        transition="cut",
        fx=["twinkle", ("confetti", dict(seed=3))],
        cam=Cam(zoom=(1.0, 1.0), punch=[.2]),
        dur=1.8,
        actors=[
            Actor("giao_su", 960, 600, enter=None, talk=True, idle="hop", kw=dict(pose="cheer")),
            Actor("chu", 960, 150, enter="pop", kw=dict(text="BẮT ĐẦU!", size=120, color=(255, 214, 80))),
        ],
    ),
]

KET = [
    Scene(
        say="Bạn thích câu hỏi nào nhất? Hãy bình luận cho mình biết, và đừng quên *đăng ký kênh* nhé!",
        fx=["twinkle", ("rays", dict(x=960, y=560, color=(24, 36, 74), speed=.3)), ("confetti", dict(seed=5))],
        cam=Cam(zoom=(1.08, 1.0)),
        dur=6.5,
        actors=[
            Actor("giao_su", 900, 600, enter="rise", talk=True, idle="hop", kw=dict(pose="cheer")),
            Actor("dau_hoi", 380, 300, enter="pop", enter_at=.5, idle="wiggle", scale=.8, flip=True),
            Actor("nut_dang_ky", 1500, 420, enter="pop", enter_at=3.0, idle="pulse"),
            Actor("sao", 1700, 290, enter="pop", enter_at=3.3, idle="wiggle"),
        ],
    ),
]

SCENES = MO_DAU + gom(__file__, TAP) + KET
