# This is for an example purpose

## this is for building image and push to lambda, don't forget to create ecr repo first

if os=window, then run this in cmd befor building docker image, after that find the example in ecr console
```bash
set DOCKER_BUILDKIT=0
```

## this is for step-function

```json
{
  "Comment": "Step Function with Distributed Map and Final Output",
  "StartAt": "FanOutMap",
  "States": {
    "FanOutMap": {
      "Type": "Map",
      "ItemsPath": "$.longterm_ids",
      "MaxConcurrency": 200,
      "ResultPath": "$.map_results",
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "DISTRIBUTED",
          "ExecutionType": "STANDARD"
        },
        "StartAt": "InvokeLambda",
        "States": {
          "InvokeLambda": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
              "FunctionName": "<your-lambda-function>",
              "Payload": {
                "longterm_id.$": "$"
              }
            },
            "ResultSelector": {
              "Payload.$": "$.Payload"
            },
            "Retry": [
              {
                "ErrorEquals": [
                  "Lambda.ServiceException",
                  "Lambda.AWSLambdaException",
                  "Lambda.SdkClientException",
                  "Lambda.TooManyRequestsException"
                ],
                "IntervalSeconds": 1,
                "MaxAttempts": 3,
                "BackoffRate": 2
              }
            ],
            "End": true
          }
        }
      },
      "Next": "ReturnResults"
    },
    "ReturnResults": {
      "Type": "Pass",
      "Parameters": {
        "status": "success",
        "results.$": "$.map_results"
      },
      "End": true
    }
  }
}
```