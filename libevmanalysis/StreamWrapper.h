#pragma once

#include <boost/iostreams/filtering_streambuf.hpp>
#include <fstream>
#include <memory>
#include <ostream>


namespace dev
{
class StreamWrapper
{
public:
    explicit StreamWrapper(
        const std::string& filepath, std::ios_base::openmode openMode = std::ios_base::app);

    std::ostream& getStream() { return *m_streamPtr; }

private:
    std::shared_ptr<std::ostream> m_streamPtr;
    std::shared_ptr<std::ofstream> m_filePtr;
    std::shared_ptr<boost::iostreams::filtering_ostreambuf> m_ostreamBuf;
};

}  // namespace dev