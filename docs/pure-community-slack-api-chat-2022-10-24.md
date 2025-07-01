Nick Veenstra (NL, University of Groningen)
  7:00 AM
@Brian Plauborg
 could you take a look at issue 89521? There seems to be some confusion now about the documentation for the "old" and "new" api
7:01
now that in 525 the crud api is out of testing, we seem to missing the documentation for the "old" one
7:04
as soon as 
@Petra Dickhaut (NL, Eindhoven University of Technology)
 types in puretest.tue.nl/ws, the 524 api is shown while the client is at 525. Annette seems to have the old and new api docs mixed up? (edited) 
Brian Plauborg
  7:55 AM
Hi Nick, I think there is a typo in the issue number, the one you listed is around DataMonitor? The 524 WS version will remain until the Pure API is fully done and most clients have migrated. Currently we redirect /ws to the newest version of the WS, though eventually that will of course be changed.
Nick Veenstra (NL, University of Groningen)
  2 months ago
sorry its 89852
Brian Plauborg
  2 months ago
That helped :slightly_smiling_face: I agree that the reference to the new API likely isn't super helpful when you were asking about access to the old one. That said, as you also mention, https://puretest.tue.nl/ws will redirect to the latest old web-service, so that is likely more useful in this case
