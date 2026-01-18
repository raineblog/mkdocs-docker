import requests
from urllib.parse import quote
import xmlrpc.client

# ================= 配置区域 (请修改这里) =================
SITE_HOST = "raineblog.dpdns.org"
SITE_URL = "https://raineblog.dpdns.org"
SITE_NAME = "RainPPR's WHK Wiki"

RSS_URL = "https://raineblog.dpdns.org/whk/feed_rss_updated.xml"
FEED_URL = "https://raineblog.dpdns.org/whk/feed_json_updated.json"
SITEMAP_URL = "https://raineblog.dpdns.org/whk/sitemap.xml"

ENCODED_URL = quote(SITE_URL)
ENCODED_NAME = quote(SITE_NAME)
ENCODED_SITEMAP = quote(SITEMAP_URL)

INDEXNOW_KEY = "3f5e21c2643f47168fc4a7cc837c7359"
INDEXNOW_KEY_LOCATION = f"https://{SITE_HOST}/{INDEXNOW_KEY}.txt"

PING_LIST = {
    # "Google": f"http://www.google.com/ping?sitemap={ENCODED_SITEMAP}",
    # "Bing": f"https://www.bing.com/ping?sitemap={ENCODED_SITEMAP}",
    # "Sogou": f"http://ping.sogou.com/ping?sitemap={ENCODED_SITEMAP}",
    # "FeedBurner": f"http://www.feedburner.com/fb/a/pingSubmit?bloglink={ENCODED_URL}",
    "Yandex": f"http://blogs.yandex.ru/pings/?blogname={ENCODED_NAME}&blogurl={ENCODED_URL}"
}

INDEXNOW_LIST = {
    "IndexNow": "https://api.indexnow.org/indexnow",
    "Bing": "https://www.bing.com/indexnow",
    "Yandex": "https://yandex.com/indexnow"
}

RPC_LIST = [
    "http://rpc.pingomatic.com",
    # "http://blogsearch.google.com/ping/RPC2",
    # "http://ping.feedburner.com"
]

# =======================================================

class SeoSubmitter:
    def __init__(self, feed_data):
        self.feed = feed_data
        self.urls = [item['url'] for item in self.feed.get('items', [])]
        print(f"[*] 成功加载 Feed，共发现 {len(self.urls)} 篇文章。")

    def submit_to_indexnow(self):
        for name, endpoint in INDEXNOW_LIST.items():

            payload = {
                "host": SITE_HOST,
                "key": INDEXNOW_KEY,
                "keyLocation": INDEXNOW_KEY_LOCATION,
                "urlList": self.urls
            }
            
            headers = {"Content-Type": "application/json; charset=utf-8"}
            
            try:
                response = requests.post(endpoint, json=payload, headers=headers)
                if response.status_code in [200, 202]:
                    print(f"[+] {name} IndexNow 推送成功: 已提交 {len(self.urls)} 个 URL。")
                else:
                    print(f"[-] {name} IndexNow 推送失败: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"[-] {name} IndexNow 连接异常: {e}")

    def submit_to_ping(self):
        for name, ping_url in PING_LIST.items():
            try:
                response = requests.get(ping_url)
                if response.status_code == 200:
                    print(f"[+] {name} Sitemap Ping 成功发出。")
                else:
                    print(f"[-] {name} Ping 状态码: {response.status_code}")
            except Exception as e:
                print(f"[-] {name} Ping 异常: {e}")

    def submit_to_websub(self):
        endpoint = "https://pubsubhubbub.appspot.com/"
        
        data = {
            "hub.mode": "publish",
            "hub.url": RSS_URL
        }
        
        try:
            r = requests.post(endpoint, data=data)
            if r.status_code in [200, 202, 204]:
                print(f"[+] WebSub 通知成功。")
            else:
                print(f"[-] WebSub 通知失败: {r.status_code}")
        except Exception as e:
            print(f"[-] WebSub 错误: {e}")

    def submit_to_xml_rpc_broadcast(self):
        for rpc_endpoint in RPC_LIST:
            try:
                server = xmlrpc.client.ServerProxy(rpc_endpoint)
                result = server.weblogUpdates.extendedPing(SITE_NAME, SITE_URL, RSS_URL)
                print(f"[+] RPC {rpc_endpoint} 响应: {result}")
            except Exception as e:
                print(f"[-] RPC {rpc_endpoint} 失败: {e}")

# ================= 主程序 =================

def main():
    try:
        response = requests.get(FEED_URL)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[-] 获取 Feed 数据失败: {e}")
        return

    submitter = SeoSubmitter(data)
    
    print("\n--- 开始执行 SEO 增强方案 ---")
    submitter.submit_to_indexnow() 
    submitter.submit_to_ping()
    submitter.submit_to_bing_batch()
    submitter.submit_to_bing_sitemap()
    submitter.submit_to_websub()
    submitter.submit_to_xml_rpc_broadcast()
    print("\n--- 执行完毕 ---")

if __name__ == "__main__":
    main()
