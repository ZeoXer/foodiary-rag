# API doc

## Base API route

https://foodiary-rag.zeoxer.com

## Methods

<details>
 <summary><code>POST</code> <code><b>/</b></code> <code>chatWithBot</code></summary>

### Parameters

> | name       | type     | data type | description |
> | ---------- | -------- | --------- | ----------- |
> | user_id    | required | string    | 用戶 ID     |
> | query_text | required | string    | 提問內容    |

### Responses

> | http code | response              |
> | --------- | --------------------- |
> | `200`     | JSON object (content) |
> | `400`     | JSON object (error)   |

</details>

<details>
 <summary><code>GET</code> <code><b>/</b></code> <code>getChatRecords/{user_id}</code></summary>

### Parameters

> | name      | type     | data type | description                          |
> | --------- | -------- | --------- | ------------------------------------ |
> | timestamp | required | float     | 前次獲取訊息的最早時間 (預設為 None) |

### Responses

> | http code | response              |
> | --------- | --------------------- |
> | `200`     | JSON object (content) |
> | `400`     | JSON object (error)   |

</details>
