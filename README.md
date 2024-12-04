# API doc

## Base API route

https://foodiary-rag.zeoxer.com

## Methods

<details>
 <summary><code>POST</code> <code><b>/</b></code> <code>chatWithBot</code></summary>

### Body Parameters

> | name       | type     | data type | description |
> | ---------- | -------- | --------- | ----------- |
> | user_id    | required | string    | 用戶 ID     |
> | query_text | required | string    | 提問內容    |

### Responses

> | http code | response              |
> | --------- | --------------------- |
> | `200`     | JSON object (content) |
> | `400`     | JSON object (error)   |

### Example

> ```shell
> curl -X POST -H "Content-Type: application/json" --data '{ "user_id": "user_0", "query_text": "請推薦一份適合運動過後食用的食物組合" }' https://foodiary-rag.zeoxer.com/chatWithBot
> ```

</details>

<details>
 <summary><code>GET</code> <code><b>/</b></code> <code>getChatRecords/{user_id}</code></summary>

### Query Parameters

> | name      | type     | data type | description                          |
> | --------- | -------- | --------- | ------------------------------------ |
> | timestamp | required | float     | 前次獲取訊息的最早時間 (預設為 None) |

### Responses

> | http code | response              |
> | --------- | --------------------- |
> | `200`     | JSON object (content) |
> | `400`     | JSON object (error)   |

### Example

> ```shell
> curl -X GET -H "Content-Type: application/json" https://foodiary-rag.zeoxer.com/getChatRecords/user_0?timestamp=
> ```

</details>
