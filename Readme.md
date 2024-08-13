# Seita optimization & software engineering assignment

Thanks for taking the time to apply at Seita Energy Flexibility! This task is the technical part of the application procedure.

This task hopefully takes not more than half a day. Of course, perfection easily takes more. What we really want is to discuss the results and your choices. You can stop after half a day ― we'll be interested in discussing how well you spent that time, looking at usable results.

We are looking for somebody who will help our team to work on and improve our core value engine ― the schedule optimizer.

The task tests some linear programming skills (translating a user requirement into an optimization model), but as we build software that runs in the wild on a daily basis, and we do that in a team, it also tests your software engineering skills.

## Form

We'd like you to put your code in a git repository on the web. This can be GitHub, Gitlab or Bitbucket etc.
Great if it's public (putting yourself out there is good!) but if you can't, then we prefer a closed repository on GitHub, where you add our accounts, so we are able to read.

The code should be self-contained, apart from dependencies.
There should be a Readme telling us what to see and do.

## The task

We want you to build an API endpoint for GETting a battery schedule as JSON response.
We provide an underlying script which implements a basic version of the scheduler. So you don't need to start from scratch.

The following three things are what we hope you to demonstrate and to discuss with you:

1. Some (API) programming
2. Understand the implemented scheduling logic
3. Be able to extend it

You might need to manage your time (and features to work on) so that each of them can be discussed (recall our earlier point about perfection).

As said above, we have prepared [an example script](example_script.py) with scheduling logic to be used. It solves the following problem:

- A battery is charged at 20% at midnight and must be maximally charged 24 hours later.
- The battery's state of charge must remain between 10% and 90%.
- The charge/discharge capacity is 10 kW.
- The storage capacity is 100 kWh.
- Find the cheapest charging/discharging schedule given a set of hourly consumption prices and production prices.

As target audience for the API endpoints, you can think about frontend developers wanting to show the responses to users. They don't know Python.

You have free choice of tooling (libraries / frameworks), as long as you use Python3 and Pyomo, and return JSON.

You might choose to (partially) use the stack of supporting libraries we are developing within Seita (e.g. Flask, Pandas etc. - the stack it's open source and documented), but you don't have to.
Most of all, we want you to deliver something that works, so we can discuss it.


## Case 1: GET /schedule

Given the relevant parameters ("soc-start", "soc-min", "soc-max", "soc-target", "storage-capacity", "power-capacity" and "conversion-efficiency", all floats), return the minimized total charging costs and the corresponding charging schedule (power and SoC).

Note: The example script does not use the `storage-capacity` yet.

There might be situations (set forth by the parameters) when the scheduler encounters an infeasible problem. We should show a meaningful error message. Bonus if we can indicate what is wrong (beyond "your parameters are infeasible), extra bonus for testing some edge case.  


## Case 2: GET /schedule?top-up=true

In the example script, the maximum charge at the end of the schedule is currently just 90 kWh (so not really fully charged).

Adjust the model to be able to top up to the full storage capacity (i.e. 100 kWh), while keeping the state of charge below 90% most of the time.

How would you document this new feature to users?


## Deliverables

Some things we take into consideration when we rate this assignment:

* The first two priorities are of course that the logic behaves *correctly* (input leads to the correct output) and that the API calls are *fast* (they do not take longer than necessary to return ― imagine this is being called hundreds or thousands of time per hour). But there are more priorities, and they do matter a lot for successful software development, see below.
* The endpoints should be demonstrable by you. But they should also be easy to start up for us (to see if they work). So please include clear instructions for somebody who is not you how to run this toy application (this begins with installing dependencies).
* Both endpoints need clear documentation for users (think of the frontend developers mentioned above), at least in the docstring. How to use, what inputs look like, what to expect if things go well and what if they don't.
* Testing is crucial. Time might not allow you to test all aspects, but please provide unit tests which test the basic behaviour. They should use dummy test data, like in the example script.
