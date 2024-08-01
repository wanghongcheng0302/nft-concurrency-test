from locust import HttpUser, task, between, events, TaskSet, constant
import random


class V1Tasks(TaskSet):
    @task(1)
    def detail(self):
        with self.client.get("/v1/mystery-box/detail/", catch_response=True, timeout=3) as resp:
            if resp.status_code == 200:
                print(f"盲盒详情: {resp.text}")

    @task(1)
    def create_order(self):
        with self.client.get("/v1/mystery-box/order/", catch_response=True, timeout=3) as resp:
            if resp.status_code == 200:
                order_id = int(resp.text)
                print(f"下单成功: {order_id}")

                action = random.choices(
                    population=["weixin_callback", "user_cancle_order", "do_nothing"],
                    weights=[80, 10, 10],
                    k=1,
                )[0]

                if action == "weixin_callback":
                    self.weixin_callback(order_id)
                elif action == "user_cancle_order":
                    self.user_cancle_order(order_id)

    def weixin_callback(self, order_id: int):
        with self.client.get(
            f"/v1/mystery-box/order-callback/",
            data={"order_id": order_id},
            catch_response=True,
        ) as resp:
            print(f"支持成功返回值: {resp.text}")

    def user_cancle_order(self, order_id: int):
        with self.client.get(
            f"/v1/mystery-box/order-cancle/",
            data={"order_id": order_id},
            catch_response=True,
        ) as resp:
            print(f"取消订单返回值: {resp.text}")


class V1User(HttpUser):
    tasks = [V1Tasks]
    wait_time = between(1, 3)
    host = "http://127.0.0.1:8080"
