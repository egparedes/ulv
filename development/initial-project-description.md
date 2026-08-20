The goal of this project is to develop a web-based tool to visualize and inspect performance benchmarks.

The web-based visualization should be extracted from the ASV AirSpeed Velocity Python framework
(available at https://github.com/airspeed-velocity/asv and locally extracted to `external/asv`).
ASV includes also the tooling to define benchmarks, run them and collect the results, but this
project explicitly ignores the definition and running parts, and only cares about the visualization.

The benchmarks results data supported by this tool should be either original result data from ASV
or data collected by Bencher (https://bencher.dev/) and available as the Bencher metric format
(https://bencher.dev/docs/reference/bencher-metric-format/) or as the results of their REST API
calls (documentation available at https://bencher.dev/docs). The tool should we executed as a
CLI tool that generates static HTML that can be hosted anywhere with a pure HTTP server like
GitHub Pages, (that is, without dynamic content). 

Analyze the project goal and the given sources and references, asking questions if some of the
requirements are unclear. Once the problem is understood, design the architecture of the system
and a implementation plan. The architecture should allow plugin other performance benchmarks
formats, and other result visualization generators besides HTML, although for now only HTML
is required.


