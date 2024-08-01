from wujie_nft_server.app import app
import time


@app.route("/v2/mystery-box/detail/")
def mystery_box_detail_v2():
    time.sleep(0.05)
    return "盲盒详情"


@app.route("/v2/mystery-box/order/")
def mystery_box_order_v2():
    time.sleep(0.1)
    return "盲盒下单"


@app.route("/v2/mystery-box/order-callback/")
def mystery_box_order_callback_v2():
    time.sleep(0.1)
    return "盲盒下单回调"
