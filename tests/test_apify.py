import os
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()
client = ApifyClient(os.getenv("APIFY_API_KEY"))

# Prepare the Actor input
run_input = {
    "startUrls": [{"url": "https://www.fierceelectronics.com/"}],
    "useSitemaps": False,
    "crawlerType": "playwright:adaptive",
    "includeUrlGlobs": [],
    "excludeUrlGlobs": [],
    "keepUrlFragments": False,
    "ignoreCanonicalUrl": False,
    "maxCrawlDepth": 20,
    "maxCrawlPages": 100,
    "initialConcurrency": 0,
    "maxConcurrency": 50,
    "initialCookies": [],
    "proxyConfiguration": {"useApifyProxy": True},
    "maxSessionRotations": 10,
    "maxRequestRetries": 5,
    "requestTimeoutSecs": 60,
    "minFileDownloadSpeedKBps": 128,
    "dynamicContentWaitSecs": 10,
    "waitForSelector": "",
    "softWaitForSelector": "",
    "maxScrollHeightPixels": 5000,
    "keepElementsCssSelector": "",
    "removeElementsCssSelector": """nav, footer, script, style, noscript, svg, img[src^='data:'],
[role=\"alert\"],
[role=\"banner\"],
[role=\"dialog\"],
[role=\"alertdialog\"],
[role=\"region\"][aria-label*=\"skip\" i],
[aria-modal=\"true\"]""",
    "removeCookieWarnings": True,
    "expandIframes": True,
    "clickElementsCssSelector": '[aria-expanded="false"]',
    "htmlTransformer": "readableText",
    "readableTextCharThreshold": 100,
    "aggressivePrune": False,
    "debugMode": False,
    "debugLog": False,
    "saveHtml": False,
    "saveHtmlAsFile": True,
    "saveMarkdown": True,
    "saveFiles": False,
    "saveScreenshots": False,
    "maxResults": 9999999,
    "clientSideMinChangePercentage": 15,
    "renderingTypeDetectionPercentage": 10,
}


def run_crawler():
    run = client.actor("aYG0l9s7dbB7j3gbS").call(run_input=run_input)


# def view():
#     dataset_items = client.dataset(dataset_id).list_items().get("items", [])

#     for item in client.dataset(run["defaultDatasetId"]).iterate_items():
#         print(item)


if __name__ == "__main__":
    run_crawler()
