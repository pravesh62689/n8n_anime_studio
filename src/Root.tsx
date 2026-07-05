import { Composition } from "remotion";
import { RhymeVideo } from "./RhymeVideo";
import { StoryVideo } from "./StoryVideo";
import { timeline, trackFrames, FPS } from "./lib";

export const Root: React.FC = () => (
  <>
    <Composition
      id="RhymeVideo"
      component={RhymeVideo}
      durationInFrames={trackFrames(timeline.rhyme)}
      fps={FPS}
      width={1920}
      height={1080}
    />
    <Composition
      id="StoryVideo"
      component={StoryVideo}
      durationInFrames={trackFrames(timeline.story)}
      fps={FPS}
      width={1920}
      height={1080}
    />
  </>
);
