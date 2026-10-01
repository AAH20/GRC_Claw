-- Array of source names with types. Replace these with your ACTUAL source names in OBS.
local sources = {
  {name = "ImageSource - MyImage.png", type = "image"},
  {name = "VideoSource - MyVideo.mp4", type = "video"},
  {name = "CameraSource - Webcam", type = "camera"},
  {name = "AudioSource - Microphone", type = "audio"},
  {name = "BrowserSource - MyWebsite", type = "browser_source"},
  {name = "MediaSource - MyStream", type = "media_source"},
  {name = "GameCapture - MyGame", type = "game_capture"}
}

-- Index of the currently visible source.
local currentSourceIndex = 1
local timer -- Declare timer globally so we can remove it later
local initialized = false  -- Flag to prevent multiple initializations


-- Function to switch to the next source.
local function switchSources()
    -- ... (your existing switchSources function code remains the same)
end

-- Function to initialize the script and set up the timer AFTER OBS has loaded.
local function initialize()
    if initialized then return end  -- Prevent multiple calls
    initialized = true

    print("OBS Finished Loading, performing initialization...")
    timer = obs.timer.new(3000, switchSources)
    timer:start()

      -- Set initial visibility (hide all except the first one)
    for i = 1, #sources do
        local source = obs.obs_source_get_by_name(sources[i].name)
        if source then
            obs.obs_source_set_visible(source, i == 1)
        else
            print("WARNING: Source not found: " .. sources[i].name)
        end
    end
end


-- Use a signal handler to call initialize() after the sources have been created
obs.obs_frontend_add_event_callback(function(event)
  if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED then  -- Or OBS_FRONTEND_EVENT_FINISHED_LOADING
    initialize()
  end
end)

--script unload function to handle timer removal
function script_unload()
  if timer then
      obs.timer.remove(timer) -- Remove the timer to prevent crashes when stopping/reloading the script
  end
end




print("Script loaded. Waiting for OBS to finish loading...")
