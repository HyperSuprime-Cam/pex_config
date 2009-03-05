// -*- lsst-c++ -*-
/**
 * @file PolicyWriter.h
 * @ingroup pex
 * @brief the definition of the PolicyWriter class
 * @author Ray Plante
 */

#ifndef LSST_PEX_POLICY_POLICYWRITER_H
#define LSST_PEX_POLICY_POLICYWRITER_H

#include "lsst/pex/policy/Policy.h"
#include <ostream>

#define NULL_FILENAME "/dev/null"

namespace lsst {
namespace pex {
namespace policy {

// forward declaration
class PolicyFile;

/**
 * An abstract interface for writing policy data to streams
 */
class PolicyWriter {
public: 

    /**
     * create a writer attached to an output stream
     * @param out     the output stream to write data to
     */
    PolicyWriter(std::ostream *out = 0);

    /**
     * delete this writer
     */
    virtual ~PolicyWriter();

    /**
     * write the contents of a policy the attached stream.  Each top-level
     * parameter will be recursively printed.
     * @param policy     the policy data to write
     * @param doDecl     if true, precede the data with the appropriate 
     *                     file format type. 
     */
    virtual void write(const Policy& policy, bool doDecl=false);

    //@{
    /**
     * write the given property out as policy data
     * @param name    the name to save the property as.  This may be a 
     *                  hierarchical name; however, an implementation is 
     *                  not guaranteed to support it.  If it cannot, 
     *                  it should raise an exception.
     * @param value   the value to save under that name.
     */
    virtual void write(const std::string& name, bool value);
    virtual void write(const std::string& name, int value);
    virtual void write(const std::string& name, double value);
    virtual void write(const std::string& name, const std::string& value);
    virtual void write(const std::string& name, const Policy& value);
    virtual void write(const std::string& name, const PolicyFile& value);
    //@}

    //@{
    /**
     * write an array of property values with a given name
     * @param name    the name to save the values as.  This may be a 
     *                  hierarchical name; however, an implementation is 
     *                  not guaranteed to support it.  If it cannot, 
     *                  it should raise an exception.
     * @param values   the values to save under that name.
     */
    virtual void write(const std::string& name, 
                       const Policy::BoolArray& values) = 0;
    virtual void write(const std::string& name, 
                       const Policy::IntArray& values) = 0;
    virtual void write(const std::string& name, 
                       const Policy::DoubleArray& values) = 0;
    virtual void write(const std::string& name, 
                       const Policy::StringArray& values) = 0;
    virtual void write(const std::string& name, 
                       const Policy::PolicyPtrArray& values) = 0;
    virtual void write(const std::string& name, 
                       const Policy::FilePtrArray& values) = 0;
    //@}

private:
    std::ostream *_nullos;
protected:

    /**
     * the output stream.  This should always be non-null.
     */
    std::ostream *_os;
};




}}}  // end namespace lsst::pex::policy

#endif // LSST_PEX_POLICY_POLICYWRITER_H

