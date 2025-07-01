# Read-Write API Notes

## Links

* [Pure API Home](https://doc.pure.elsevier.com/display/PUREAPI/Pure+API+Home)
* Schema 
  * [https://experts.umn.edu/ws/api/openapi.yaml](https://experts.umn.edu/ws/api/openapi.yaml)
  * [https://experts.umn.edu/ws/api/openapi.json](https://experts.umn.edu/ws/api/openapi.json)
* Interactive Swagger docs: [https://experts.umn.edu/ws/api/api-docs/index.html](https://experts.umn.edu/ws/api/api-docs/index.html?url=/ws/api/openapi.yaml)
* Non-interactive docs: [https://experts.umn.edu/ws/api/documentation/index.html](https://experts.umn.edu/ws/api/documentation/index.html)
* []()
* []()

## Design Ideas

* Add a new `mode` attribute to the `Config` class.
  * Defaults to `rw` for read-write.
  * Other valid value is `r`, for read-only. 
* For attribute defaults, prepend read-only-specific values with `r_`.
  * Eventually, these will be deprecated and then go away.
* Schemas
  * Put read-only schemas in `schemas/r/`.
  * Put read-write schemas in `schemas/`.
  * Continue to put schemas in sub-directories named for Pure versions, so we can compare them and test against them.
* Testing
  * Maybe switch to testing against JSON paths in records from different versions, instead of testing transformers?
  * [jsonpath-ng](https://github.com/h2non/jsonpath-ng) looks promising.
